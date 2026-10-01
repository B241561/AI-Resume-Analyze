import logging
import sys
import types

import pytest

import config


SECRET = "gsk_test_SECRET_123"
KEY = (config.KEYRING_SERVICE, config.KEYRING_ACCOUNT)


@pytest.fixture
def fake_keyring(monkeypatch):
    store = {}

    errors = types.ModuleType("keyring.errors")

    class PasswordDeleteError(Exception):
        pass

    errors.PasswordDeleteError = PasswordDeleteError

    kr = types.ModuleType("keyring")

    kr.errors = errors

    kr.get_password = (
        lambda service, account:
        store.get((service, account))
    )

    kr.set_password = (
        lambda service, account, pw:
        store.__setitem__((service, account), pw)
    )

    def delete_password(service, account):
        if (service, account) not in store:
            raise PasswordDeleteError()
        del store[(service, account)]

    kr.delete_password = delete_password

    monkeypatch.setitem(
        sys.modules,
        "keyring",
        kr,
    )

    monkeypatch.setitem(
        sys.modules,
        "keyring.errors",
        errors,
    )

    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )

    return store


def test_service_and_account_unchanged():
    assert config.KEYRING_SERVICE == "AI Resume Analyzer"
    assert config.KEYRING_ACCOUNT == "groq_api_key"


def test_keyring_value_available(fake_keyring):
    fake_keyring[KEY] = SECRET

    assert config.get_groq_api_key() == SECRET
    assert config.get_groq_key_source() == "secure storage"


def test_env_value_available(fake_keyring, monkeypatch):
    monkeypatch.setenv(
        "GROQ_API_KEY",
        SECRET,
    )

    assert config.get_groq_api_key() == SECRET
    assert config.get_groq_key_source() == "GROQ_API_KEY"


def test_keyring_precedence_over_env(
    fake_keyring,
    monkeypatch,
):
    fake_keyring[KEY] = "from_keyring"

    monkeypatch.setenv(
        "GROQ_API_KEY",
        "from_env",
    )

    assert config.get_groq_api_key() == "from_keyring"


def test_whitespace_stripped(
    fake_keyring,
    monkeypatch,
):
    fake_keyring[KEY] = f"  {SECRET}\n"

    assert config.get_groq_api_key() == SECRET

    fake_keyring.clear()

    monkeypatch.setenv(
        "GROQ_API_KEY",
        f"  {SECRET}  ",
    )

    assert config.get_groq_api_key() == SECRET


def test_empty_env_is_unavailable(
    fake_keyring,
    monkeypatch,
):
    monkeypatch.setenv(
        "GROQ_API_KEY",
        "   ",
    )

    assert config.get_groq_api_key() == ""
    assert config.get_groq_key_source() is None


def test_whitespace_keyring_falls_back_to_env(
    fake_keyring,
    monkeypatch,
):
    fake_keyring[KEY] = "   "

    monkeypatch.setenv(
        "GROQ_API_KEY",
        "from_env",
    )

    assert config.get_groq_api_key() == "from_env"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        "\n\t",
        None,
    ],
)
def test_empty_save_rejected(
    fake_keyring,
    bad,
):
    with pytest.raises(ValueError):
        config.save_groq_api_key(bad)

    assert KEY not in fake_keyring


def test_save_success_strips(fake_keyring):
    config.save_groq_api_key(
        f"  {SECRET}  "
    )

    assert fake_keyring[KEY] == SECRET


def test_remove_success(fake_keyring):
    fake_keyring[KEY] = SECRET

    config.remove_stored_groq_api_key()

    assert KEY not in fake_keyring


def test_remove_when_absent(fake_keyring):
    config.remove_stored_groq_api_key()


def test_remove_does_not_touch_other_entries(
    fake_keyring,
):
    fake_keyring[KEY] = SECRET
    fake_keyring[("Other App", "token")] = "keep"

    config.remove_stored_groq_api_key()

    assert (
        fake_keyring[("Other App", "token")]
        == "keep"
    )


def test_no_credential_leakage(
    fake_keyring,
    monkeypatch,
    caplog,
    capsys,
):
    caplog.set_level(logging.DEBUG)

    monkeypatch.setenv(
        "GROQ_API_KEY",
        SECRET,
    )

    config.save_groq_api_key(SECRET)
    config.get_groq_api_key()
    config.get_groq_key_source()
    config.remove_stored_groq_api_key()

    with pytest.raises(ValueError) as exc:
        config.save_groq_api_key("   ")

    out = capsys.readouterr()

    assert SECRET not in caplog.text
    assert SECRET not in out.out + out.err
    assert SECRET not in str(exc.value)
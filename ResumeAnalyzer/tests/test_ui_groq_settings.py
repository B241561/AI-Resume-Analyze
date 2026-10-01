import tkinter
from unittest import mock

import customtkinter as ctk
import pytest

import analyzer
import ui

SECRET = "gsk_test_SECRET_123"

MESSAGES = {
    "authentication": "Groq authentication failed. Check GROQ_API_KEY.",
    "model_unavailable": "Groq model unavailable. Check GROQ_MODEL.",
    "quota_or_rate_limit": "Groq quota or rate limit reached. Try again later.",
    "network": "Groq network request failed. Check your connection.",
    "malformed_response": "Groq returned an invalid response. Try again.",
    "unknown_provider_error": "Groq request failed. Check the model and connection.",
}


# ---------- helper-level tests (no display needed) ----------

def test_connection_success_calls_only_connection_test():
    with mock.patch.object(ui, "test_groq_connection", return_value=None) as conn, \
         mock.patch.object(ui, "analyze_resume") as analyze:
        ok, message = ui.run_groq_connection_test(SECRET)
    conn.assert_called_once_with(SECRET)
    analyze.assert_not_called()
    assert ok is True
    assert "successful" in message.lower()
    assert SECRET not in message


@pytest.mark.parametrize("category", list(MESSAGES))
def test_connection_error_categories(category):
    err = analyzer.GroqRequestError(category)
    with mock.patch.object(ui, "test_groq_connection", side_effect=err):
        ok, message = ui.run_groq_connection_test(SECRET)
    assert ok is False
    assert message == MESSAGES[category]
    assert SECRET not in message


def test_malformed_response_error_maps_to_invalid_response():
    with mock.patch.object(ui, "test_groq_connection", side_effect=analyzer.GroqMalformedResponseError()):
        ok, message = ui.run_groq_connection_test(SECRET)
    assert not ok and message == MESSAGES["malformed_response"]


@pytest.mark.parametrize("exc", [
    ValueError(f"boom {SECRET}"),
    TypeError(f"boom {SECRET}"),
    RuntimeError(f"boom {SECRET}"),
])
def test_unknown_errors_sanitized_and_not_malformed(exc):
    with mock.patch.object(ui, "test_groq_connection", side_effect=exc):
        ok, message = ui.run_groq_connection_test(SECRET)
    assert not ok
    assert message == MESSAGES["unknown_provider_error"]
    assert SECRET not in message


def test_save_checked_success():
    with mock.patch.object(ui, "save_groq_api_key") as save, \
         mock.patch.object(ui, "get_stored_groq_api_key", return_value=SECRET):
        assert ui.save_groq_key_checked(f"  {SECRET}  ") is True
    save.assert_called_once_with(SECRET)


@pytest.mark.parametrize("bad", ["", "   ", None])
def test_save_checked_rejects_empty(bad):
    with mock.patch.object(ui, "save_groq_api_key") as save:
        assert ui.save_groq_key_checked(bad) is False
    save.assert_not_called()


def test_save_checked_fails_when_keyring_raises():
    with mock.patch.object(ui, "save_groq_api_key", side_effect=RuntimeError("x")):
        assert ui.save_groq_key_checked(SECRET) is False


def test_save_checked_fails_when_not_persisted():
    with mock.patch.object(ui, "save_groq_api_key"), \
         mock.patch.object(ui, "get_stored_groq_api_key", return_value=""):
        assert ui.save_groq_key_checked(SECRET) is False


def test_local_fallback_without_key():
    with mock.patch.object(analyzer, "get_groq_api_key", return_value=""):
        result = analyzer.analyze_resume("Python developer\nSkills: Python, SQL", "", use_groq=True)
    assert result["analysis_mode"] == "Local analysis"
    assert result["match_percentage"] is None


# ---------- widget-level tests (need a display) ----------

def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


@pytest.fixture
def app_env(monkeypatch):
    state = {"key": "", "source": None, "stored": ""}
    monkeypatch.setattr(ui, "get_groq_api_key", lambda: state["key"])
    monkeypatch.setattr(ui, "get_groq_key_source", lambda: state["source"])
    monkeypatch.setattr(ui, "get_stored_groq_api_key", lambda: state["stored"])
    monkeypatch.setattr(ui, "list_recent_analyses", lambda: [])
    apps = []

    def make():
        try:
            app = ui.ResumeAnalyzerApp()
        except tkinter.TclError:
            pytest.skip("No display available")
        app.withdraw()
        apps.append(app)
        return app

    yield state, make
    for app in apps:
        app.destroy()


def _open_dialog(app):
    app._show_groq_settings()
    dialog = [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)][-1]
    entry = next(w for w in _walk(dialog) if isinstance(w, ctk.CTkEntry))

    def button(text):
        return next(w for w in _walk(dialog) if isinstance(w, ctk.CTkButton) and w.cget("text") == text)

    return dialog, entry, button


def test_no_key(app_env):
    state, make = app_env
    app = make()
    assert app.groq_checkbox.cget("state") == "disabled"
    assert app.use_groq_var.get() is False
    assert "Not configured" in app.groq_status_label.cget("text")


def test_key_configured_secure_storage(app_env):
    state, make = app_env
    state.update(key=SECRET, source="secure storage", stored=SECRET)
    app = make()
    assert app.groq_checkbox.cget("state") == "normal"
    assert "Configured via secure storage" in app.groq_status_label.cget("text")


def test_key_configured_env_only_remove_disabled(app_env):
    state, make = app_env
    state.update(key=SECRET, source="GROQ_API_KEY", stored="")
    app = make()
    assert "GROQ_API_KEY" in app.groq_status_label.cget("text")
    assert app.groq_remove_button.cget("state") == "disabled"


def test_dialog_title(app_env):
    _state, make = app_env
    app = make()
    dialog, _entry, _button = _open_dialog(app)
    assert dialog.title() == "Groq AI Settings"
    dialog.destroy()


def test_save_key_refreshes_status(app_env, monkeypatch):
    state, make = app_env
    app = make()

    def fake_save(key):
        state.update(key=key, source="secure storage", stored=key)

    monkeypatch.setattr(ui, "save_groq_api_key", fake_save)
    monkeypatch.setattr(ui.messagebox, "showinfo", lambda *a, **k: None)
    dialog, entry, button = _open_dialog(app)
    entry.insert(0, f"  {SECRET}  ")
    button("Save").invoke()
    assert app.groq_checkbox.cget("state") == "normal"
    assert app.use_groq_var.get() is True
    assert "Configured via secure storage" in app.groq_status_label.cget("text")


def test_save_empty_not_saved(app_env, monkeypatch):
    _state, make = app_env
    app = make()
    save = mock.Mock()
    warn = mock.Mock()
    monkeypatch.setattr(ui, "save_groq_api_key", save)
    monkeypatch.setattr(ui.messagebox, "showwarning", warn)
    dialog, _entry, button = _open_dialog(app)
    button("Save").invoke()
    save.assert_not_called()
    warn.assert_called_once()
    dialog.destroy()


def test_show_hide_only_toggles_visibility(app_env):
    _state, make = app_env
    app = make()
    dialog, entry, button = _open_dialog(app)
    entry.insert(0, SECRET)
    toggle = button("Show")
    assert entry._entry.cget("show") == "•"
    toggle.invoke()
    assert entry._entry.cget("show") == "" and toggle.cget("text") == "Hide"
    toggle.invoke()
    assert entry._entry.cget("show") == "•" and toggle.cget("text") == "Show"
    assert entry.get() == SECRET
    dialog.destroy()


def test_dialog_test_connection_uses_stripped_key(app_env, monkeypatch):
    _state, make = app_env
    app = make()
    conn = mock.Mock(return_value=None)
    info = mock.Mock()
    monkeypatch.setattr(ui, "test_groq_connection", conn)
    monkeypatch.setattr(ui.messagebox, "showinfo", info)
    dialog, entry, button = _open_dialog(app)
    entry.insert(0, f"  {SECRET}  ")
    button("Test Connection").invoke()
    conn.assert_called_once_with(SECRET)
    assert info.call_args[0][0] == "Connection successful"
    dialog.destroy()


def test_dialog_test_connection_error_is_sanitized(app_env, monkeypatch):
    _state, make = app_env
    app = make()
    monkeypatch.setattr(ui, "test_groq_connection", mock.Mock(side_effect=ValueError(f"x {SECRET}")))
    err = mock.Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", err)
    dialog, entry, button = _open_dialog(app)
    entry.insert(0, SECRET)
    button("Test Connection").invoke()
    shown = err.call_args[0][1]
    assert shown == MESSAGES["unknown_provider_error"]
    assert SECRET not in shown
    dialog.destroy()


def test_remove_key_without_env_disables_groq(app_env, monkeypatch):
    state, make = app_env
    state.update(key=SECRET, source="secure storage", stored=SECRET)
    app = make()
    remove = mock.Mock(side_effect=lambda: state.update(key="", source=None, stored=""))
    monkeypatch.setattr(ui, "remove_stored_groq_api_key", remove)
    monkeypatch.setattr(ui.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(ui.messagebox, "showinfo", lambda *a, **k: None)
    app._remove_groq_key()
    remove.assert_called_once()
    assert app.groq_checkbox.cget("state") == "disabled"
    assert app.use_groq_var.get() is False
    assert app.groq_remove_button.winfo_manager() == ""


def test_remove_key_with_env_fallback_keeps_groq(app_env, monkeypatch):
    state, make = app_env
    state.update(key=SECRET, source="secure storage", stored=SECRET)
    app = make()
    monkeypatch.setattr(
        ui, "remove_stored_groq_api_key",
        lambda: state.update(key="env_key", source="GROQ_API_KEY", stored=""),
    )
    monkeypatch.setattr(ui.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(ui.messagebox, "showinfo", lambda *a, **k: None)
    app._remove_groq_key()
    assert app.groq_checkbox.cget("state") == "normal"
    assert "GROQ_API_KEY" in app.groq_status_label.cget("text")
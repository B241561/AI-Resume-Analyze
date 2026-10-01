from __future__ import annotations

import logging

from config import BASE_DIR, ensure_app_directories
from database import initialize_database
from ui import ResumeAnalyzerApp


def configure_logging() -> None:
    log_path = BASE_DIR / "app.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    ensure_app_directories()
    configure_logging()
    initialize_database()
    app = ResumeAnalyzerApp()
    app.mainloop()


if __name__ == "__main__":
    main()

"""Launch a dedicated persistent Chrome or attach to an explicit debug instance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app_generator.config import GeneratorConfig
from app_generator.errors import BrowserError


@dataclass
class ChromeSession:
    config: GeneratorConfig
    driver: Any | None = None

    def start(self) -> Any:
        try:
            from selenium import webdriver
        except ImportError as exc:
            raise BrowserError("Selenium is not installed. Run: python -m pip install -r requirements-generator.txt") from exc
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        if self.config.browser_mode == "controlled":
            self.config.chrome_profile_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f"--user-data-dir={self.config.chrome_profile_dir}")
        else:
            options.debugger_address = self.config.debugger_address
        try:
            self.driver = webdriver.Chrome(options=options)
        except Exception as exc:
            mode = "dedicated profile" if self.config.browser_mode == "controlled" else "debugger address"
            raise BrowserError(f"Chrome could not start using the configured {mode}: {exc}") from exc
        return self.driver

    def close(self) -> None:
        if self.driver is not None:
            try:
                if self.config.browser_mode == "controlled":
                    self.driver.quit()
                elif getattr(self.driver, "service", None) is not None:
                    self.driver.service.stop()
            finally:
                self.driver = None

    def __enter__(self) -> Any:
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.close()

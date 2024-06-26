"""Data7 configuration module."""

from typing import List

from dynaconf import Dynaconf

SETTINGS_FILES: List[str] = ["settings.yaml", ".secrets.yaml", "data7.yaml"]

settings = Dynaconf(
    envvar_prefix="DATA7",
    root_path=".",
    settings_files=SETTINGS_FILES,
    environments=True,
    load_dotenv=True,
)

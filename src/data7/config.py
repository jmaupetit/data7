"""Data7 configuration module."""

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DATA7",
    root_path=".",
    settings_files=["settings.yaml", ".secrets.yaml", "data7.yaml"],
    environments=True,
    load_dotenv=True,
)

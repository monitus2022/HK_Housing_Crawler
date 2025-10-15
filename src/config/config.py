from pathlib import Path
from dynaconf import Dynaconf

working_dir = Path(__file__).parent.parent.parent
config_path = working_dir / "config" / "config.yml"

housing_crawler_config = Dynaconf(
    environments=True,
    envvar_prefix="HK_HOUSING",
    settings_files=[str(config_path)],
    merge_enabled=True
)

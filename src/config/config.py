from pathlib import Path
from typing import Dict
import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

working_dir = Path(__file__).parent.parent.parent
config_path = working_dir / "src" / "config" / "config.yml"

with open(config_path, 'r', encoding='utf-8') as f:
    yaml_data = yaml.safe_load(f)

class AgencyUrls(BaseModel):
    all_estate_info: str
    single_estate_info: str
    estate_monthly_market_info: str
    building_transactions: str
    legacy_building_transactions: str
    legacy_building_ids: str

class AgencyApi(BaseModel):
    urls: AgencyUrls
    headers: Dict[str, str]
    cookies_token: str

class DatabaseFileNames(BaseModel):
    duckdb: str
    sqlite: str

class DatabaseTableNames(BaseModel):
    estate_info: str

class Databases(BaseModel):
    path: str
    file_names: DatabaseFileNames
    table_names: DatabaseTableNames

class FilesOutputs(BaseModel):
    transactions_db: str
    estate_info_json: str
    estate_id_json: str
    building_id_json: str
    building_info_json: str
    legacy_transaction_csv: str

class Files(BaseModel):
    path: str
    outputs: FilesOutputs

class Storage(BaseModel):
    root_path: str
    databases: Databases
    files: Files

class Config(BaseSettings):
    agency_api: AgencyApi
    storage: Storage

    model_config = SettingsConfigDict(
        extra="allow"
    )

housing_crawler_config = Config(**yaml_data)


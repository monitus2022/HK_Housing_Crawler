import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from logger import housing_logger

class HeadersAgency(BaseModel):
    accept: str = Field(..., description="Accept header")
    accept_language: str = Field(..., description="Accept-Language header")
    authorization: str = Field(..., description="Bearer token for auth")
    origin: str = Field(..., description="Origin header")
    referer: str = Field(..., description="Referer header")
    sec_ch_ua: str = Field(..., description="Sec-CH-UA header")
    sec_ch_ua_mobile: str = Field(..., description="Sec-CH-UA-Mobile header")
    sec_ch_ua_platform: str = Field(..., description="Sec-CH-UA-Platform header")
    sec_fetch_dest: str = Field(..., description="Sec-Fetch-Dest header")
    sec_fetch_mode: str = Field(..., description="Sec-Fetch-Mode header")
    sec_fetch_site: str = Field(..., description="Sec-Fetch-Site header")
    sec_gpc: str = Field(..., description="Sec-GPC header")
    user_agent: str = Field(..., description="User-Agent header")

class FilePathsAgency(BaseModel):
    db: str
    estate_info_json: str
    estate_id_json: str
    building_id_json: str
    transactions_json: str

class UrlsAgency(BaseModel):
    estate_info: str
    estate_market_info: str
    building_transactions: str
    legacy_building_transactions: str
    legacy_building_ids: str

class Database(BaseModel):
    table_names: dict[str, str]  # e.g., {"estate_info": "estate_info"}

class Headers(BaseModel):
    agency: HeadersAgency

class FilePaths(BaseModel):
    agency: FilePathsAgency
    
class Urls(BaseModel):
    agency: UrlsAgency
    
class HousingCrawlerConfig(BaseModel):
    """
    Top-level configuration model for the housing crawler
    """
    headers: Headers
    urls: Urls
    file_paths: FilePaths
    database: Database

# Load config from YAML
def load_config() -> HousingCrawlerConfig:
    """
    Loads the housing crawler configuration from a YAML file
    """
    config_path = Path(__file__).parent / "config.yml"
    if not config_path.exists():
        housing_logger.error(f"Configuration file not found at {config_path}")
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not data:
        housing_logger.error("Configuration file is empty or invalid.")
        raise ValueError("Configuration file is empty or invalid.")
    return HousingCrawlerConfig(**data)

# Global config instance
housing_crawler_config = load_config()

from crawlers.agency import *
from processors.agency import *
from config import housing_crawler_config

def app():
    # print(housing_crawler_config.agency_api.headers)
    housing_crawler = AgencyCrawler()
    housing_crawler.fetch_estate_id_and_info()

if __name__ == "__main__":
    app()
    
from crawlers.agency import AgencyCrawler
from processors.agency import AgencyProcessor

def app():
    housing_crawler = AgencyCrawler()
    housing_crawler.fetch_all_building_ids()

if __name__ == "__main__":
    app()
    
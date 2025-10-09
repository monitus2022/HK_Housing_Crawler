from crawlers.agency import *
from processors.agency import *

def app():
    crawler = AgencyCrawler()
    crawler.fetch_estate_id_and_info()

    processor = AgencyProcessor()
    processor.process_estate_info_json()
    processor.save_estate_info_to_db()

if __name__ == "__main__":
    app()
    
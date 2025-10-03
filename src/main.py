from crawlers.agency import *
from processors.agency import *

def app():
    crawler = AgencyCrawler()
    crawler.fetch_all_transaction_history()

    # processor = AgencyProcessor()
    # print(processor.save_estate_info_to_db())

if __name__ == "__main__":
    app()
    
from crawlers.agency import *
from processors.agency import *

def app():
    crawler = AgencyCrawler()
    crawler.fetch_estate_info()
    # processor = AgencyProcessor()
    # print(processor.fetch_estate_info())

if __name__ == "__main__":
    app()
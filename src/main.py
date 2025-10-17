from crawlers.agency import AgencyCrawler
from processors.agency import AgencyProcessor


def app():
    housing_crawler = AgencyCrawler()
    housing_crawler.fetch_estate_id_and_info(lang="zh-hk")  # Fetch estate info in Traditional Chinese


if __name__ == "__main__":
    app()

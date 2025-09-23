from crawlers.housing_agency import *

def app():
    fetch_transaction_data_given_building_id("B000063459")

if __name__ == "__main__":
    app()
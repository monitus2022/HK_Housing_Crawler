from crawlers.agency import *
from processors.agency import *

def app():
    processor = AgencyProcessor()
    processor.save_estate_info_to_db(
        db_type="sqlite" 
    )

if __name__ == "__main__":
    app()
    
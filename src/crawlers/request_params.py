FETCH_ESTATE_INFO_PARAMS = {
            "hash": "true",
            "lang": "en",
            "currency": "HKD",
            "unit": "feet",
            "search_behavior": "normal",
            "limit": 1000,
            "page": 1,
        }

FETCH_ESTATE_MARKET_INFO_PARAMS = {
            "type": "estate",
            "lang": "en",
            "monthly": "true",
            "id": None,  # to be filled in dynamically
        }

FETCH_ESTATE_MONTHLY_MARKET_INFO_PARAMS = {
            "type": "estate",
            "lang": "en",
            "monthly": "true",
            "est_ids": None,  # to be filled in dynamically
        }

SIMPLE_FETCH_PARAMS = {
    "lang": "en"
}
# Note: Split transaction json into 4 tables
# 1. Building Info
# 2. Unit info
# 3. Unit features
# 4. Transaction info per unit

BUILDING_INFO_TABLE_SCHEMA = {
    "estate_id": "TEXT",
    "estate_name": "TEXT",
    "building_id": "TEXT",
    "building_name": "TEXT",
    "phase_id": "TEXT",
    "phase_name": "TEXT"
}

UNIT_INFO_TABLE_SCHEMA = {
    "building_id": "TEXT",
    "building_name": "TEXT",
    "unit_id": "TEXT",
    "floor": "TEXT",
    "floor_seq": "INTEGER",
    "flat": "TEXT",
    "area": "REAL",
    "net_area": "REAL",
    "bedroom": "INTEGER",
    "sitting_room": "INTEGER"
}

UNIT_FEATURES_TABLE_SCHEMA = {
    "unit_id": "TEXT",
    "feature_id": "TEXT",
    "feature_name": "TEXT",
}

TRANSACTIONS_TABLE_SCHEMA = {
    "transaction_id": "TEXT",
    "unit_id": "TEXT",
    "price": "REAL",
    "tx_date": "TEXT",
    "last_tx_date": "TEXT",
    "gain": "REAL",
    "net_ft_price": "REAL"
}

ESTATE_MONTHLY_MARKET_SCHEMA = {
    "estate_id": "TEXT",
    "date": "TEXT",
    "avg_ft_price": "REAL",
    "avg_net_ft_price": "REAL",
    "avg_ft_rent": "REAL",
    "avg_net_ft_rent": "REAL",
    "max_ft_price": "REAL",
    "max_net_ft_price": "REAL",
    "max_ft_rent": "REAL",
    "max_net_ft_rent": "REAL",
    "min_ft_price": "REAL",
    "min_net_ft_price": "REAL",
    "min_ft_rent": "REAL",
    "min_net_ft_rent": "REAL",
    "total_tx_count": "INTEGER",
    "total_rent_tx_count": "INTEGER",
    "total_tx_amount": "REAL",
    "total_rent_tx_amount": "REAL",
    "pre_avg_ft_price": "REAL",
    "pre_avg_net_ft_price": "REAL",
    "pre_avg_ft_rent": "REAL",
    "pre_avg_net_ft_rent": "REAL",
    "pre_max_ft_price": "REAL",
    "pre_max_net_ft_price": "REAL",
    "pre_max_ft_rent": "REAL",
    "pre_max_net_ft_rent": "REAL",
    "pre_min_ft_price": "REAL",
    "pre_min_net_ft_price": "REAL",
    "pre_min_ft_rent": "REAL",
    "pre_min_net_ft_rent": "REAL",
    "pre_total_tx_count": "INTEGER",
    "pre_total_rent_tx_count": "INTEGER",
    "pre_total_tx_amount": "REAL",
    "pre_total_rent_tx_amount": "REAL",
    "avg_ft_price_chg": "REAL",
    "avg_net_ft_price_chg": "REAL",
    "avg_ft_rent_chg": "REAL",
    "avg_net_ft_rent_chg": "REAL",
    "circulate_rate": "REAL",
    "pre_circulate_rate": "REAL",
    "total_no_of_unit": "INTEGER",
    "pre_total_no_of_unit": "INTEGER"
}
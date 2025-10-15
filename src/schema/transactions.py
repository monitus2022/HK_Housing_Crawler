# Note: Split transaction json into 2 tables
# 1. Building Info
# 2. Unit info
# 3. Transaction info per unit

BUILDING_INFO_TABLE_SCHEMA = {
    "estate_id": "TEXT",
    "estate_name": "TEXT",
    "building_id": "TEXT",
    "building_name": "TEXT",
    "phase_id": "TEXT",
    "phase_name": "TEXT",
    "unit_count": "INTEGER",
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

TRANSACTIONS_TABLE_SCHEMA = {
    "transaction_id": "TEXT",
    "estate_id": "TEXT",
    "building_id": "TEXT",
    "unit_id": "TEXT",
    "price": "REAL",
    "tx_date": "TEXT",
    "last_tx_date": "TEXT",
    "gain": "REAL",
    "net_ft_price": "REAL"
}

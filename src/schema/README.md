## HK Housing Crawler - API Endpoint and Examples

### 1. All Estate Info
- **Endpoint:** `all_estate_info`
- Description: Fetches a list of all estates with basic information, including estate IDs, names, and locations.
- Example URL: https://data.hkp.com.hk/search/v1/estates?hash=true&lang=en&currency=HKD&unit=feet&search_behavior=normal&limit=10&page=1

### 2. Single Estate Info
- **Endpoint:** `single_estate_info`
- Description: Fetches detailed information about a specific estate. Include list of buildings/phases belonged to the estate.
- Example URL: https://data.hkp.com.hk/info/v1/estates/E000004419?lang=en

### 3. Estate Monthly Market Info
- **Endpoint:** `estate_monthly_market_info`
- Description: Fetches monthly market information for a specific estate.
- Example URL: https://data.hkp.com.hk/info/v1/market_stat?lang=en&type=estate&monthly=true&est_ids=E000004419

### 4. Building Transactions
- **Endpoint:** `building_transactions`
- Description: Fetches transaction records for each units in a specific building/phase.
- Example URL: https://data.hkp.com.hk/info/v1/transactions/buildings/B000063458?lang=zh-hk&firsthand=false
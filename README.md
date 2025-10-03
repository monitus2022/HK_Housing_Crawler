# HK_Housing_Crawler

A web crawler for scraping housing data in Hong Kong using traditional web scraping techniques.

## Specs

- Crawling frequency:
  - Transaction data: Daily
  - Aggregated data: Weekly
- Data sources:
    - [Hong Kong Property](https://www.hkp.com.hk/zh-hk/list/estate)
    - [Rating and Valuation Department, Hong Kong Gov](https://www.rvd.gov.hk/en/publications/property_market_statistics.html)
- Data storage: SQLite database
- Data usage: For data visualization and chatbot application

## Setup

1. Clone the repository.
2. Create a virtual env:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the crawler:
```bash
python src/main.py
```

## Disclaimer

This project is for educational purposes only.
All data sourced from Hong Kong Property is public and used in accordance with their [Terms of Service](https://www.hkp.com.hk/disclaim.html).

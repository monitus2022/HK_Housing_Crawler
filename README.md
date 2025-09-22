# HK_Housing_Crawler

A web crawler for scraping housing data in Hong Kong using traditional web scraping techniques.

## Specs

- Crawling frequency:
  - Transaction data: Daily
  - Aggregated data: Weekly
- Data sources:
    - [Centaline Property Agency Limited](https://hk.centanet.com/estate/en/index)
    - [Rating and Valuation Department](https://www.rvd.gov.hk/en/publications/property_market_statistics.html)
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
Ensure compliance with the terms of service of the websites you scrape.
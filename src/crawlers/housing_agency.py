import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def fetch_transaction_data():
    
    url = """
    https://app2.hkp.com.hk/utx/tx_history.jsp?bldg_id=B000000048&est_id=E00024&phase_id=P000000790&street_id=&house=false&lang=en
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    table = soup.find('table', {'id': 'Tx_hist_table'})
    thead = table.find('thead')
    headers = [
        th.get_text(strip=True) for th in thead.find_all('th')
    ]

    data = []
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.get_text(strip=True) for ele in cols]
        data.append(cols)
    df = pd.DataFrame(data, columns=headers)
    df.to_csv('transactions.csv', index=False)

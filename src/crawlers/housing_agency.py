import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# TODO: Add error handling and type safe with pydantic

def fetch_transaction_data_given_building_id(building_id):
    """
    Fetch transaction data for a given building ID
    """
    url = f"https://app2.hkp.com.hk/utx/tx_history.jsp?bldg_id={building_id}&lang=en"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Parse the fullpage table
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

def fetch_building_ids_given_estate_id(estate_id):
    """
    Fetch building IDs for a given estate ID.
    """
    url = f"https://app2.hkp.com.hk/utx/index.jsp?est_id={estate_id}&lang=zh"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Left side building list per estate
    rows = soup.find_all("tr", {"class": "bldg_NotCurr"})

    building_data = []
    for row in rows:
        link = row.find("a")
        if link:
            # Get building ID
            building_url = link["href"]
            building_id_match = re.search(r'bldg_id=(B\d+)', building_url)
            building_id = building_id_match.group(1) if building_id_match else None
            
            # Split name by <br/> tag
            for br in link.find_all('br'):
                br.replace_with('|')
            
            full_name = link.get_text(strip=True)
            estate_unit, building_name = full_name.split('|') if '|' in full_name else (full_name, '')
            
            building_data.append({
                'building_id': building_id,
                'block_name': estate_unit.strip(),
                'building_name': building_name.strip()
            })
            
    return building_data

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import json

# TODO: Add error handling and type safe with pydantic

def fetch_transaction_data_given_building_id(building_id):
    """
    Fetch transaction data for a given building ID (e.g. B000063459)
    """
    base_url = f"https://app2.hkp.com.hk/utx/tx_history.jsp"
    params = {
        "bldg_id": building_id,
        "lang": "en",
    }
    response = requests.get(base_url, params=params)
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
    Fetch building IDs for a given estate ID. (e.g. E00024)
    """
    base_url = f"https://app2.hkp.com.hk/utx/index.jsp"
    params = {
        "est_id": estate_id,
        "lang": "zh",
    }
    response = requests.get(base_url, params=params)
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

def fetch_estate_ids():
    """
    Fetch all estate IDs from the paginated API. Contains all info for each estate.
    """
    
    base_url = "https://data.hkp.com.hk/search/v1/estates"
    params = {
        "hash": "true",
        "lang": "zh-hk",
        "currency": "HKD",
        "unit": "feet",
        "search_behavior": "normal",
        "limit": 1000,
        "page": 1
    }
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.8",
        "authorization": None, # Insert your token here
        "origin": "https://www.hkp.com.hk",
        "referer": "https://www.hkp.com.hk/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    estate_count = float('inf')
    all_estates = []
    
    while params["page"] * params["limit"] <= estate_count:
        response = requests.get(base_url, 
                                params=params,
                                headers=headers
                                )
        
        if response.status_code != 200:
            print(f"Error fetching page {params['page']}: {response.status_code}")
            break
            
        data = response.json()
        if not data or len(data) == 0:
            break

        estate_data = data["result"]
        all_estates.extend(estate_data)
        print(f"Fetched page {params['page']}, got {len(estate_data)} estates")
        
        # Fix fetch size
        if estate_count == float('inf'):
            estate_count = data.get("count", float('inf'))
            print(f"Total estates to fetch: {estate_count}")
        params["page"] += 1
        
        time.sleep(1)
    
    with open("estate_info.json", "w", encoding="utf-8") as f:
        json.dump(all_estates, f, ensure_ascii=False, indent=4)
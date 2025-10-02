import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import json
from logger import housing_logger

# TODO: Type safe with pydantic

class AgencyCrawler:
    def __init__(self):
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.8",
            "authorization": "Bearer " + "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJndWlkIjoibXItMjAyNS0wOS0yMS1NX193MFh3VFF3RjI0R1ZWNUo3Yy1OYUhnQU5ZR2h5WngteTV4MThDN254SmNUVXhqeUFhVmEtWFZvN0NZclc3SDlJU2tXaS1JSSIsImlhdCI6MTc1ODQ2NTIwNCwiaXNzIjoid3d3LmhrcC5jb20uaGsifQ.c9ME2M6G7vQDwZuX9eyEwFoYa7S64ZW4wUQONnMd5QdL2XVg5xeVFQfyzq5OtylLLa2VRSlT6xpgS513ptq9bHDvZrHrr0egBMtgvvvpnG03r66TUZBiY7PeBWkYbIMmQiUbGyHB2FRhlEJfezrXPspa6ZvCYUkYiPlu-8IvzD7x79vJMfIB9q2htYGI6mfvd9F8wkAjAnTYSKUjyy1hM-1VFTEChf4BY7du5WPJ2buJYW_3DZ_vkOnB5FZt60d7pgTIhYpqMykoYkHq3aOj8bE-I-Gzt1tb9Hq0q7xojEeABiuwH2ffVR3p8zqHN1g3ht70tkSdzfoXb45K8J858Oqcwzs9vlV0RJ30x2lhN5LEdrbdpMj-A1rhxkXvg_6HHqcUC5aafZdo9H0vpq3kt1ixsoRIJZi2wxUFxzag2XPc6T7_uEC5Nop2x1JCZpeTGGi2rwzJhmDJodoSxWMw0ffOFcgposXPWoFOlLWp2MDOJ4kSViOj0R-R6jXrsy1EsFbFWjlTVaNLcuL8i0IAIeZhB1vmlasdyxxAGZb4LESwKcgqJawlsiPg_c_y-whc1cUXIsHosjSlP92_s2RmiEk7ybRMLxdtRqLweZ478nEPBX6YoS4WFSy2D_8uSzKapjDQMWM3YkM8vcNKXPv2I6QI87UqZ0CNIvrDdhXDcd4", # Insert your token here via https://www.hkp.com.hk/zh-hk/list/estate
            "origin": "https://www.hkp.com.hk",
            "referer": "https://www.hkp.com.hk/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        }
        # Init session to persist headers and cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(
        self,
        url: str,
        params: dict = None,
    ):
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            housing_logger.error(f"Error making request to {url}: {str(e)}")
            return None

    def fetch_transaction_history_given_building_id(self, building_id):
        """
        Fetch transaction history for a given building ID (e.g. B000063459)
        """
        base_url = f"https://data.hkp.com.hk/info/v1/transactions/buildings/{building_id}"
        params = {"lang": "en"}
        response = self._make_request(
            base_url, 
            params=params
            )
        if not response:
            return None
        data = response.json()
        return data

    def fetch_estate_market_info_given_estate_id(self, estate_id):
        """
        Fetch market info for a given estate ID (e.g. E00024)
        """
        base_url = f"https://data.hkp.com.hk/info/v1/market_stat"
        params = {
            "type": "estate",
            "lang": "en",
            "monthly": "true",
            "id": estate_id,
        }
        response = self._make_request(
            base_url, 
            params=params
            )
        if not response:
            return None
        data = response.json()
        return data

    def fetch_estate_id_and_info(self):
        """
        Fetch all estate IDs and info from the paginated API.
        """
        base_url = "https://data.hkp.com.hk/search/v1/estates"
        params = {
            "hash": "true",
            "lang": "zh-hk",
            "currency": "HKD",
            "unit": "feet",
            "search_behavior": "normal",
            "limit": 1000,
            "page": 1,
        }
        estate_count = float("inf")
        all_estates = []
        estate_ids = []

        while params["page"] * params["limit"] <= estate_count:
            response = self._make_request(
                base_url, 
                params=params
                )

            if response.status_code != 200:
                housing_logger.error(f"Error fetching page {params['page']}: {response.status_code}")
                break

            data = response.json()
            if not data or len(data) == 0:
                break

            estate_data = data["result"]
            all_estates.extend(estate_data)
            housing_logger.info(f"Fetched page {params['page']}, got {len(estate_data)} estates")

            # Fix fetch size
            if estate_count == float("inf"):
                estate_count = data.get("count", float("inf"))
                housing_logger.info(f"Total estates to fetch: {estate_count}")
            params["page"] += 1

            # Collect estate IDs for further processing
            estate_ids.extend([estate["id"] for estate in estate_data])

            time.sleep(1)

        with open("estate_info.json", "w", encoding="utf-8") as f:
            json.dump(all_estates, f, ensure_ascii=False, indent=4)
        
        with open("estate_ids.json", "w", encoding="utf-8") as f:
            json.dump(estate_ids, f, ensure_ascii=False, indent=4)

    def _legacy_fetch_transaction_data_given_building_id(self, building_id):
        """
        Fetch transaction data for a given building ID (e.g. B000063459)
        Does not work on latest buildings with Phase IDs
        """
        base_url = "https://app2.hkp.com.hk/utx/tx_history.jsp"
        params = {
            "bldg_id": building_id,
            "lang": "en",
        }
        response = self._make_request(
            base_url, 
            params=params,
            headers=self.headers
            )
        if not response:
            return

        soup = BeautifulSoup(response.content, "html.parser")

        # Parse the fullpage table
        table = soup.find("table", {"id": "Tx_hist_table"})
        thead = table.find("thead")
        headers = [th.get_text(strip=True) for th in thead.find_all("th")]

        data = []
        tbody = table.find("tbody")
        if not tbody:
            housing_logger.warning(f"No transaction data found for building ID {building_id}")
            return
        rows = tbody.find_all("tr")
        if not rows:
            housing_logger.warning(f"No transaction data found for building ID {building_id}")
            return
        for row in rows:
            cols = row.find_all("td")
            cols = [ele.get_text(strip=True) for ele in cols]
            data.append(cols)
        df = pd.DataFrame(data, columns=headers)
        df.to_csv("transactions.csv", index=False)
        
    def _legacy_fetch_building_ids_given_estate_id(self, estate_id):
        """
        Fetch building IDs for a given estate ID. (e.g. E00024)
        Does not work on latest estates with Phase IDs
        """
        base_url = f"https://app2.hkp.com.hk/utx/index.jsp"
        params = {
            "est_id": estate_id,
            "lang": "zh",
        }
        response = self._make_request(
            base_url, 
            params=params,
            headers=self.headers
            )
        if not response:
            return []
        soup = BeautifulSoup(response.content, "html.parser")

        # Left side building list per estate
        rows = soup.find_all("tr", {"class": "bldg_NotCurr"})
        rows += soup.find_all("tr", {"class": "bldg_Curr"})

        building_data = []
        for row in rows:
            link = row.find("a")
            if link:
                # Get building ID
                building_url = link["href"]
                building_id_match = re.search(r"bldg_id=(B\d+)", building_url)
                building_id = building_id_match.group(1) if building_id_match else None

                # Split name by <br/> tag
                for br in link.find_all("br"):
                    br.replace_with("|")

                full_name = link.get_text(strip=True)
                estate_unit, building_name = (
                    full_name.split("|") if "|" in full_name else ("", full_name)
                )

                building_data.append(
                    {
                        "building_id": building_id,
                        "block_name": estate_unit.strip(),
                        "building_name": building_name.strip(),
                    }
                )
        return building_data
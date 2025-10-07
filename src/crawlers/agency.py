import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import json
from config import housing_crawler_config
from logger import housing_logger
import pathlib
from typing import Optional

# TODO: Type safe with pydantic


class AgencyCrawler:
    def __init__(self):
        self.headers = housing_crawler_config.headers.agency.model_dump()
        # Ensure data directory exists
        data_dir = pathlib.Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Init session to persist headers and cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        self.estate_info_file_path = housing_crawler_config.file_paths.agency.estate_info_json
        self.estate_id_file_path = housing_crawler_config.file_paths.agency.estate_id_json
        self.building_id_file_path = housing_crawler_config.file_paths.agency.building_id_json
        self.transactions_file_path = housing_crawler_config.file_paths.agency.transactions_json

    def _make_request(self, url: str, params: dict = None) -> Optional[requests.Response]:
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            housing_logger.error(f"Error making request to {url}: {str(e)}")
            return None

    def fetch_all_transaction_history(self):
        """
        Fetch transaction history for all building IDs listed in all_building_ids.json
        """
        with open(self.building_id_file_path, "r", encoding="utf-8") as f:
            building_ids = json.load(f)
        all_transactions = []
        output_path = housing_crawler_config.file_paths.agency.transactions_json
        housing_logger.info(
            f"Starting to fetch transaction history for {len(building_ids)} buildings"
        )

        for idx, building_id in enumerate(building_ids):
            building_data = self.fetch_transaction_history_given_building_id(
                building_id
            )
            if building_data and building_data.get("data", []):
                building_data["data"] = self.clean_single_building_transaction_data(
                    building_data.get("data", [])
                )
                all_transactions.append(building_data)
            # Save progress every 100 buildings
            if idx != 0 and idx % 100 == 0:
                with open(output_path, "w", encoding="utf-8") as out_f:
                    json.dump(all_transactions, out_f, ensure_ascii=False, indent=2)
                housing_logger.info(
                    f"Fetched transaction history for {idx+1}/{len(building_ids)} buildings so far"
                )
            time.sleep(0.25)

    @staticmethod
    def clean_single_building_transaction_data(data) -> list[dict]:
        """
        Remove unnecessary fields from a single building transaction data to reduce storage size
        Further processing can be done in the processor class
        Args:
            data (list): Raw transaction data from 'data' field for a single building
        """
        for flat_unit in data:
            flat_unit.pop("unit_id", None)
            flat_unit.pop("unit_type", None)
            if not flat_unit["transactions"]:
                continue
            flat_unit["transactions"] = [
                {
                    k: v
                    for k, v in tx.items()
                    if k not in ["id", "tx_type", "feature", "url_desc"]
                }
                for tx in flat_unit.get("transactions", [])
            ]
        return data

    def fetch_transaction_history_given_building_id(self, building_id) -> Optional[dict[str, list|dict]]:
        """
        Fetch transaction history for a given building ID (e.g. B000063459)
        """
        base_url = housing_crawler_config.urls.agency.building_transactions + f"/{building_id}"
        params = {"lang": "en"}
        response = self._make_request(base_url, params=params)
        if not response:
            return None
        data = response.json()
        return data

    def fetch_all_building_ids(self) -> None:
        """
        Fetch all building IDs from all estates listed in estate_ids.json
        """
        with open(housing_crawler_config.file_paths.agency.estate_id_json, "r", encoding="utf-8") as f:
            estate_ids = json.load(f)
        all_building_ids = []
        output_path = housing_crawler_config.file_paths.agency.estate_info_json
        housing_logger.info(
            f"Starting to fetch building IDs for {len(estate_ids)} estates"
        )

        for idx, estate_id in enumerate(estate_ids):
            _, building_ids = self.fetch_estate_info_and_building_ids_given_estate_id(estate_id)
            if building_ids:
                all_building_ids.extend(building_ids)
            # Save progress every 100 estates
            if idx != 0 and idx % 100 == 0:
                with open(output_path, "w", encoding="utf-8") as out_f:
                    json.dump(all_building_ids, out_f, ensure_ascii=False, indent=2)
                housing_logger.info(
                    f"Fetched building IDs for {idx+1}/{len(estate_ids)} estates so far"
                )
            time.sleep(0.25)

    def fetch_estate_info_and_building_ids_given_estate_id(self, estate_id) -> Optional[tuple[dict, list]]:
        """
        Fetch estate info and building IDs for a given estate ID (e.g. E00024)
        """
        base_url = housing_crawler_config.urls.agency.estate_info + f"/{estate_id}"
        params = {"lang": "en"}
        response = self._make_request(base_url, params=params)
        if not response:
            return None
        data = response.json()
        building_ids = []
        for phase in data.get("phase", []):
            building_ids.extend(
                [b.get("id") for b in phase.get("buildings", []) if "id" in b]
            )
        # TODO: Currently using building ids for transaction history fetch only
        return {"estate_info": None}, building_ids

    def fetch_estate_market_info_given_estate_id(self, estate_id):
        """
        Fetch market info for a given estate ID (e.g. E00024)
        """
        base_url = housing_crawler_config.urls.agency.estate_market_info
        params = {
            "type": "estate",
            "lang": "en",
            "monthly": "true",
            "id": estate_id,
        }
        response = self._make_request(base_url, params=params)
        if not response:
            return None
        data = response.json()
        return data

    def fetch_estate_id_and_info(self) -> None:
        """
        Fetch all estate IDs and info from the paginated API and output to json.
        """
        base_url = housing_crawler_config.urls.agency.estate_info
        params = {
            "hash": "true",
            "lang": "en",
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
            response = self._make_request(base_url, params=params)

            if response.status_code != 200:
                housing_logger.error(
                    f"Error fetching page {params['page']}: {response.status_code}"
                )
                break

            data = response.json()
            if not data or len(data) == 0:
                break

            estate_data = data["result"]
            all_estates.extend(estate_data)
            housing_logger.info(
                f"Fetched page {params['page']}, got {len(estate_data)} estates"
            )

            # Fix fetch size
            if estate_count == float("inf"):
                estate_count = data.get("count", float("inf"))
                housing_logger.info(f"Total estates to fetch: {estate_count}")
            params["page"] += 1

            # Collect estate IDs for further processing
            estate_ids.extend([estate["id"] for estate in estate_data])

            time.sleep(0.25)

        with open(housing_crawler_config.file_paths.agency.estate_info_json, "w", encoding="utf-8") as f:
            json.dump(all_estates, f, ensure_ascii=False, indent=4)

        with open(housing_crawler_config.file_paths.agency.estate_id_json, "w", encoding="utf-8") as f:
            json.dump(estate_ids, f, ensure_ascii=False, indent=4)

    def _legacy_fetch_transaction_data_given_building_id(self, building_id):
        """
        Fetch transaction data for a given building ID (e.g. B000063459)
        Does not work on latest buildings with Phase IDs
        """
        base_url = housing_crawler_config.urls.agency.legacy_building_transactions
        params = {
            "bldg_id": building_id,
            "lang": "en",
        }
        response = self._make_request(base_url, params=params, headers=self.headers)
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
            housing_logger.warning(
                f"No transaction data found for building ID {building_id}"
            )
            return
        rows = tbody.find_all("tr")
        if not rows:
            housing_logger.warning(
                f"No transaction data found for building ID {building_id}"
            )
            return
        for row in rows:
            cols = row.find_all("td")
            cols = [ele.get_text(strip=True) for ele in cols]
            data.append(cols)
        df = pd.DataFrame(data, columns=headers)
        df.to_csv(housing_crawler_config.file_paths.agency.transaction_data_csv, index=False)

    def _legacy_fetch_building_ids_given_estate_id(self, estate_id):
        """
        Fetch building IDs for a given estate ID. (e.g. E00024)
        Does not work on latest estates with Phase IDs
        """
        base_url = housing_crawler_config.urls.agency.legacy_building_transactions
        params = {
            "est_id": estate_id,
            "lang": "zh",
        }
        response = self._make_request(base_url, params=params, headers=self.headers)
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

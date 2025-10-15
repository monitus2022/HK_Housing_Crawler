import requests
import time
import json
from config import housing_crawler_config
from logger import housing_logger
from typing import Optional
from .base import BaseCrawler
from processors import CrawlerProcessor
from .request_params import FETCH_ESTATE_INFO_PARAMS, SIMPLE_FETCH_PARAMS, FETCH_ESTATE_MARKET_INFO_PARAMS


class AgencyCrawler(BaseCrawler):
    """
    Crawler for HKP APIs
    Dataflow:
    1. Fetch all estate IDs and info from paginated API
    2. For each estate ID, fetch building IDs
    3. For each building ID, fetch building, unit info and transaction history
    Data will be further processed in the processor class
    """
    def __init__(self):
        super().__init__()
        self.headers = dict(housing_crawler_config.agency_api.headers)
        
        # Init session to persist headers and cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Load cookies from file and update with token from config
        # TODO: Use selenium to get fresh cookies
        with open("src/crawlers/agency_cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)
        cookies["token"] = housing_crawler_config.agency_api.cookies_token
        self.session.cookies.update(cookies)
        self._set_file_paths()
        self._set_request_urls()
        self.crawler_processor = CrawlerProcessor()

    def _set_file_paths(self) -> None:
        self.estate_info_file_path = self.files_path / housing_crawler_config.storage.files.outputs.estate_info_json
        self.estate_id_file_path = self.files_path / housing_crawler_config.storage.files.outputs.estate_id_json
        self.building_id_file_path = self.files_path / housing_crawler_config.storage.files.outputs.building_id_json
        self.transactions_file_path = self.files_path / housing_crawler_config.storage.files.outputs.transactions_json

    def _set_request_urls(self) -> None:
        self.all_estate_info_url = housing_crawler_config.agency_api.urls.all_estate_info
        self.single_estate_info_url = housing_crawler_config.agency_api.urls.single_estate_info
        self.estate_market_info_url = housing_crawler_config.agency_api.urls.estate_market_info
        self.building_transactions_url = housing_crawler_config.agency_api.urls.building_transactions

    def fetch_all_building_transactions(self) -> None:
        """
        Fetch transactions for all building IDs listed in building_ids.json
        """
        housing_logger.info("Starting to fetch all transactions for all buildings")
        # Load building IDs from file
        with open(self.building_id_file_path, "r", encoding="utf-8") as f:
            estate_building_ids = json.load(f)
        estate_ids = list(estate_building_ids.keys())
        number_of_buildings = sum(len(bids) for bids in estate_building_ids.values())
        housing_logger.info(f"Total {number_of_buildings} buildings in {len(estate_ids)} estates to fetch transactions for")
        
        # Check existing estate IDs in the database to avoid duplicates
        try:
            existing_estate_ids = self.crawler_processor.get_existing_estate_ids()
            # Remove already loaded estate IDs from the list to fetch
            estate_ids = [eid for eid in estate_ids if eid not in existing_estate_ids]
            housing_logger.info(f"Skipping {len(existing_estate_ids)} existing estates already in the database")
        except Exception as e:
            housing_logger.info("No existing estates found in the database, starting fresh.")
            existing_estate_ids = set()
            
        building_count = 0
        housing_logger.info(
            f"Starting to fetch transaction for {number_of_buildings} buildings in {len(estate_ids)} estates"
        )
        for estate_id, building_ids in estate_building_ids.items():
            if estate_id not in estate_ids:  # Skip if already processed
                continue
            for building_id in building_ids:
                try:
                    raw_data = self._fetch_transaction_history_given_building_id(building_id)
                    if raw_data:
                        self.crawler_processor.process_single_building(raw_data)
                except Exception as e:
                    housing_logger.warning(f"Failed to fetch transactions for building {building_id}: {e}")
                building_count += 1
                # Save progress every 100 buildings or at the end
                if building_count % 100 == 0 or (estate_id == estate_ids[-1] and building_id == building_ids[-1]):
                    self.crawler_processor.update_tables()
                    housing_logger.info(f"Processed {building_count} buildings so far")
                time.sleep(0.25)
        housing_logger.info(f"Fetched transactions for {building_count} buildings")

    def _legacy_fetch_all_building_transactions(self) -> None:
        """
        Fetch transactions for all building IDs listed in building_ids.json
        """
        housing_logger.info("Starting to fetch all transactions for all buildings")
        with open(self.building_id_file_path, "r", encoding="utf-8") as f:
            estate_building_ids = json.load(f)
        estate_ids = list(estate_building_ids.keys())
        number_of_buildings = sum(len(bids) for bids in estate_building_ids.values())
        housing_logger.info(f"Total {number_of_buildings} buildings in {len(estate_ids)} estates to fetch transactions for")
        all_transactions = {}

        # Check if existing transactions file exists to avoid duplicates
        output_path = self.transactions_file_path
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                all_transactions = json.load(f)
                existing_estate_ids = {list(item.keys())[0] for item in all_transactions}
                housing_logger.info(
                    f"Loaded existing transaction data for {len(existing_estate_ids)} estates from {self.transactions_file_path}"
                )
                # Remove already loaded estate IDs from the list to fetch
                estate_ids = [eid for eid in estate_ids if eid not in existing_estate_ids]
        except FileNotFoundError:
            housing_logger.info(f"No existing transaction data found at {output_path}, starting fresh.")

        # Fetch transactions for each building ID
        housing_logger.info(
            f"Starting to fetch transaction for {len(estate_ids)} estates"
        )
        batched_transactions = {}
        building_id_count = 0
        for idx, (estate_id, building_ids) in enumerate(estate_building_ids.items()):
            batched_transactions.update(estate_transaction_data)
            estate_transaction_data = self._fetch_and_process_transactions_for_estate(estate_id, building_ids)
            building_id_count += len(building_ids)
            # Save progress every 100 estates and at the end
            if idx != 0 and (idx + 1) % 100 == 0 or idx == len(estate_ids) - 1:
                all_transactions.update(batched_transactions)
                with open(output_path, "w", encoding="utf-8") as out_f:
                    json.dump(all_transactions, out_f, ensure_ascii=False, indent=2)
                batched_transactions = {}
                housing_logger.info(
                    f"Fetched transactions for {idx + 1}/{len(estate_ids)} estates, {building_id_count} buildings so far"
                )
            time.sleep(0.25)
        housing_logger.info(f"Fetched transactions for all {len(estate_ids)} estates")

    def _fetch_and_process_transactions_for_estate(self, estate_id: str, building_ids: list[str]) -> dict:
        """
        Fetch and process transactions for all buildings in a given estate
        """
        estate_transaction_data = {estate_id: {}}
        for building_id in building_ids:
            raw_data = self._fetch_transaction_history_given_building_id(building_id)
            if not raw_data:
                continue
            cleaned_data = self._clean_single_building_transaction_data(raw_data.get("data", []))
            if cleaned_data:
                estate_transaction_data[estate_id][building_id] = cleaned_data
        return estate_transaction_data

    @staticmethod
    def _clean_single_building_transaction_data(data: list[dict]) -> list[dict]:
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
                    if k not in ["tx_type", "mkt_type", "url_desc", "area", "net_area"]
                }
                for tx in flat_unit.get("transactions", [])
            ]
        return data

    def _fetch_transaction_history_given_building_id(
            self, building_id: str) -> Optional[dict[str, list|dict]]:
        """
        Fetch transaction history for a given building ID (e.g. B000063459)
        """
        base_url = self.building_transactions_url.format(building_id=building_id)
        params = SIMPLE_FETCH_PARAMS.copy()
        response = self._make_request(base_url, params=params)
        if not response:
            return None
        data = response.json()
        return data

    def fetch_all_building_ids(self) -> None:
        """
        Fetch all building IDs from all estates listed in estate_ids.json
        """
        housing_logger.info("Starting to fetch all building IDs from all estates")
        loaded_estate_ids = set()
        output_path = self.building_id_file_path
        with open(self.estate_id_file_path, "r", encoding="utf-8") as f:
            estate_ids = json.load(f)

        # If file already exists, load existing building IDs to avoid duplicates
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_building_id_data = json.load(f)
                loaded_estate_ids = set(existing_building_id_data.keys())
                housing_logger.info(
                    f"Loaded building IDs for {len(loaded_estate_ids)} existing estates from {output_path}"
                )
                # Remove already loaded estate IDs from the list to fetch
                estate_ids = [eid for eid in estate_ids if eid not in loaded_estate_ids]
        except FileNotFoundError:
            housing_logger.info(f"No existing building IDs found at {output_path}, starting fresh.")
        housing_logger.info(
            f"Starting to fetch building IDs for {len(estate_ids)} estates"
        )

        batched_building_ids = {}
        for idx, estate_id in enumerate(estate_ids):
            _, building_ids = self._fetch_estate_info_and_building_ids_given_estate_id(estate_id)
            batched_building_ids.update(building_ids)

            # Save progress every 100 estates or at the end
            if idx != 0 and (idx + 1) % 100 == 0 or idx == len(estate_ids) - 1:
                existing_building_id_data.update(batched_building_ids)
                with open(output_path, "w", encoding="utf-8") as out_f:
                    json.dump(existing_building_id_data, out_f, ensure_ascii=False, indent=2)
                batched_building_ids = {}
                housing_logger.info(
                    f"Fetched building IDs for {idx+1}/{len(estate_ids)} estates so far"
                )
            time.sleep(0.25)
        housing_logger.info(f"Saved all building IDs to {output_path}")

    def _fetch_estate_info_and_building_ids_given_estate_id(
            self, estate_id: str
            ) -> Optional[tuple[dict, dict[str, list]]]:
        """
        Fetch estate info and building IDs for a given estate ID (e.g. E00024)
        """
        base_url = self.single_estate_info_url.format(estate_id=estate_id)
        params = SIMPLE_FETCH_PARAMS.copy()
        response = self._make_request(base_url, params=params)
        if not response:
            return None
        data = response.json()

        # Extract building IDs from the nested phase -> buildings structure
        estate_id = data.get("id", "")
        building_ids = []
        for phase in data.get("phase", []):
            building_ids.extend(
                [b.get("id") for b in phase.get("buildings", []) if "id" in b]
            )
        # TODO: Currently using building ids for transaction history fetch only
        return {"estate_info": None}, {estate_id: building_ids}

    def _fetch_estate_market_info_given_estate_id(self, estate_id: str) -> Optional[dict]:
        """
        Fetch market info for a given estate ID (e.g. E00024)
        """
        base_url = self.estate_market_info_url
        params = FETCH_ESTATE_MARKET_INFO_PARAMS.copy()
        params["id"] = estate_id

        response = self._make_request(base_url, params=params)
        if not response:
            return None
        data = response.json()
        return data

    def fetch_estate_id_and_info(self) -> None:
        """
        Fetch all estate IDs and info from the paginated API and output to json.
        """
        housing_logger.info("Starting to fetch all estate IDs and info")
        base_url = self.all_estate_info_url
        params = FETCH_ESTATE_INFO_PARAMS.copy()
        estate_count = float("inf")
        all_estates = []
        estate_ids = []

        while params["page"] * params["limit"] <= estate_count:
            response = self._make_request(base_url, params=params)
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

        with open(self.estate_info_file_path, "w", encoding="utf-8") as f:
            json.dump(all_estates, f, ensure_ascii=False, indent=4)
            housing_logger.info(f"Saved estate info to {self.estate_info_file_path}")

        with open(self.estate_id_file_path, "w", encoding="utf-8") as f:
            json.dump(estate_ids, f, ensure_ascii=False, indent=4)
            housing_logger.info(f"Saved estate IDs to {self.estate_id_file_path}")

    # def _legacy_fetch_transaction_data_given_building_id(self, building_id):
    #     """
    #     Fetch transaction data for a given building ID (e.g. B000063459)
    #     Does not work on latest buildings with Phase IDs
    #     """
    #     base_url = housing_crawler_config.urls.agency.legacy_building_transactions
    #     params = {
    #         "bldg_id": building_id,
    #         "lang": "en",
    #     }
    #     response = self._make_request(base_url, params=params, headers=self.headers)
    #     if not response:
    #         return

    #     soup = BeautifulSoup(response.content, "html.parser")

    #     # Parse the fullpage table
    #     table = soup.find("table", {"id": "Tx_hist_table"})
    #     thead = table.find("thead")
    #     headers = [th.get_text(strip=True) for th in thead.find_all("th")]

    #     data = []
    #     tbody = table.find("tbody")
    #     if not tbody:
    #         housing_logger.warning(
    #             f"No transaction data found for building ID {building_id}"
    #         )
    #         return
    #     rows = tbody.find_all("tr")
    #     if not rows:
    #         housing_logger.warning(
    #             f"No transaction data found for building ID {building_id}"
    #         )
    #         return
    #     for row in rows:
    #         cols = row.find_all("td")
    #         cols = [ele.get_text(strip=True) for ele in cols]
    #         data.append(cols)
    #     df = pd.DataFrame(data, columns=headers)
    #     df.to_csv(housing_crawler_config.file_paths.agency.transaction_data_csv, index=False)

    # def _legacy_fetch_building_ids_given_estate_id(self, estate_id):
    #     """
    #     Fetch building IDs for a given estate ID. (e.g. E00024)
    #     Does not work on latest estates with Phase IDs
    #     """
    #     base_url = housing_crawler_config.urls.agency.legacy_building_transactions
    #     params = {
    #         "est_id": estate_id,
    #         "lang": "zh",
    #     }
    #     response = self._make_request(base_url, params=params, headers=self.headers)
    #     if not response:
    #         return []
    #     soup = BeautifulSoup(response.content, "html.parser")

    #     # Left side building list per estate
    #     rows = soup.find_all("tr", {"class": "bldg_NotCurr"})
    #     rows += soup.find_all("tr", {"class": "bldg_Curr"})

    #     building_data = []
    #     for row in rows:
    #         link = row.find("a")
    #         if link:
    #             # Get building ID
    #             building_url = link["href"]
    #             building_id_match = re.search(r"bldg_id=(B\d+)", building_url)
    #             building_id = building_id_match.group(1) if building_id_match else None

    #             # Split name by <br/> tag
    #             for br in link.find_all("br"):
    #                 br.replace_with("|")

    #             full_name = link.get_text(strip=True)
    #             estate_unit, building_name = (
    #                 full_name.split("|") if "|" in full_name else ("", full_name)
    #             )

    #             building_data.append(
    #                 {
    #                     "building_id": building_id,
    #                     "block_name": estate_unit.strip(),
    #                     "building_name": building_name.strip(),
    #                 }
    #             )
    #     return building_data

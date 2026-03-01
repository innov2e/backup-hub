import requests
from typing import Dict, Any, List

class KnackExtractor:
    def __init__(self, app_id: str, api_key: str, logger):
        self.app_id = app_id
        self.api_key = api_key
        self.logger = logger
        self.base_url = "https://api.knack.com/v1"

    def _headers(self) -> Dict[str, str]:
        return {
            "X-Knack-Application-Id": self.app_id,
            "X-Knack-REST-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def fetch_all_records(self, object_id: str, page_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Scarica TUTTI i record di un oggetto KNACK usando paginazione.
        """
        page = 1
        all_records: List[Dict[str, Any]] = []

        while True:
            url = f"{self.base_url}/objects/{object_id}/records"
            params = {"page": page, "rows_per_page": page_size}

            self.logger.info(f"KNACK GET {url} page={page}")
            r = requests.get(url, headers=self._headers(), params=params, timeout=60)
            r.raise_for_status()

            data = r.json()
            records = data.get("records", [])
            all_records.extend(records)

            total_pages = data.get("total_pages", 1)
            if page >= total_pages:
                break
            page += 1

        self.logger.info(f"KNACK object={object_id} records={len(all_records)}")
        return all_records

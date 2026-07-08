from dataclasses import dataclass
import time

from loguru import logger
import requests


@dataclass
class OpenAgendaClient:
    base_url: str
    page_size: int = 100
    politeness_delay: float = 0.2

    def fetch_events(
        self,
        where_clause: str,
        max_records: int = 200,
    ) -> list[dict]:
        records: list[dict] = []
        offset = 0

        while True:
            params = {
                "where": where_clause,
                "limit": self.page_size,
                "offset": offset,
                "lang": "fr",
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            batch = data.get("results", [])
            if not batch:
                break

            records.extend(batch)
            total = data.get("total_count", 0)
            logger.info(f"Fetched {len(records)}/{min(total, max_records)} events")

            if len(records) >= min(total, max_records):
                break

            offset += self.page_size
            time.sleep(self.politeness_delay)

        logger.info(f"Total events fetched: {len(records)}")
        return records

    @staticmethod
    def build_where_clause(
        region: str,
        date_from: str,
        date_to: str,
    ) -> str:
        return (
            f'location_region = "{region}"'
            f' AND firstdate_begin >= "{date_from}"'
            f' AND lastdate_begin <= "{date_to}"'
        )

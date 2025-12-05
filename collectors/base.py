import os
import logging
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

# SHARED CONFIG
DB_HOST = 'localhost'
DB_PORT = 8123
DB_USER = 'default'
DB_PASS = 'kairos'

class BaseCollector:
    def __init__(self, slug):
        self.slug = slug
        self.log = logging.getLogger(f"Kairos.{slug}")
        self.log.setLevel(logging.INFO)
        self.client = self._connect_db()

    def _connect_db(self):
        try:
            client = clickhouse_connect.get_client(
                host=DB_HOST, port=DB_PORT, username=DB_USER, password=DB_PASS
            )
            return client
        except Exception as e:
            self.log.critical(f"DB Connection Failed: {e}")
            raise

    def insert_batch(self, batch):
        """
        Expects batch to be a list of lists:
        [[timestamp, project_slug, metric_name, value], ...]
        """
        if not batch:
            return
        try:
            self.client.insert(
                'metrics', 
                batch, 
                column_names=['timestamp', 'project_slug', 'metric_name', 'metric_value']
            )
            self.log.info(f"Injected {len(batch)} records.")
        except Exception as e:
            self.log.error(f"Insert Failed: {e}")

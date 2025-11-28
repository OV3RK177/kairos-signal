from abc import ABC, abstractmethod
from datetime import datetime
import json
from kafka import KafkaProducer

class KairosCollector(ABC):
    def __init__(self, name):
        self.name = name
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
        except:
            print("⚠️ Warning: Redpanda not found. Running in local mode.")
            self.producer = None

    def send_data(self, metric_name, value, meta=None):
        payload = {
            "ts": datetime.utcnow().isoformat(),
            "source": self.name,
            "metric": metric_name,
            "value": value,
            "meta": meta or {}
        }
        if self.producer:
            self.producer.send('kairos_firehose', value=payload)
        else:
            print(f"[LOCAL] {metric_name}: {value}")
        
    @abstractmethod
    def collect(self):
        pass

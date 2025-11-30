from abc import ABC, abstractmethod
from datetime import datetime
import json
try:
    from kafka import KafkaProducer
except:
    KafkaProducer = None

class KairosCollector(ABC):
    def __init__(self, name):
        self.name = name
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
        except:
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
            try:
                self.producer.send('kairos_firehose', value=payload)
            except:
                pass
        else:
            # Fallback log if Redpanda isn't up
            pass
        
    @abstractmethod
    def collect(self):
        pass

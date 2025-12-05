import os
import logging
from itertools import cycle
from dotenv import load_dotenv

load_dotenv()

class KeyManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeyManager, cls).__new__(cls)
            cls._instance._init_keys()
        return cls._instance

    def _init_keys(self):
        self.log = logging.getLogger("Kairos.Keys")
        self.key_rings = {}
        
        # MAP: Service -> Env Var
        sources = {
            "helius": "HELIUS_API_KEY",
            "birdeye": "BIRDEYE_API_KEY",
            "polygon": "MASSIVE_API_KEY",
            "grass": "GRASS_AUTH_TOKEN",
            "dune": "DUNE_API_KEY",
            "flightaware": "FLIGHTAWARE_KEY",
            "purpleair": "PURPLEAIR_API_KEY",
            "dimo": "DIMO_API_KEY"
        }

        for service, env_var in sources.items():
            raw = os.getenv(env_var, "")
            if not raw:
                self.key_rings[service] = None
                continue

            if "," in raw:
                keys = [k.strip() for k in raw.split(",") if k.strip()]
                self.log.info(f"Loaded {len(keys)} keys for {service} (Swarm Mode).")
            else:
                keys = [raw.strip()]

            self.key_rings[service] = cycle(keys)

    def get_next(self, service):
        ring = self.key_rings.get(service)
        if not ring: return None
        return next(ring)

key_manager = KeyManager()

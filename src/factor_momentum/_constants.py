from sf_quant.data.factors import get_factor_names

from dotenv import load_dotenv
import os

load_dotenv()

TMP = os.getenv("TMP")

DROPPED_FACTORS = [
    "USSLOWL_RESVOL",
    "USSLOWL_MOMENTUM",
    "USSLOWL_BETA",
]

FACTORS = [fac for fac in get_factor_names('style')
            if fac not in DROPPED_FACTORS]

TYPES = [
    "1m cross-section",
    "12m time-series continuous",
    "12m time-series discrete",
]
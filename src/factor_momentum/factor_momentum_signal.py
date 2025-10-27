import datetime as dt
import polars as pl

from ._wrappers import factorspace_signals_monthly, assetspace_signal_monthly, alpha_monthly
from ._constants import TYPES


class FactorMomentumSignal:
    def __init__(self, type: str):
        if type not in TYPES:
            raise ValueError(
                f"Invalid type '{type}'. Must be one of these:  {', '.join(TYPES)}"
            )
        self._type = type

    def get_factorspace_signal_monthly(self, start: dt.date, end: dt.date) -> pl.DataFrame:
        return factorspace_signals_monthly(start=start, end=end, type=self._type)
    
    def get_signal_monthly(self, start: dt.date, end: dt.date) -> pl.DataFrame:
        return assetspace_signal_monthly(start=start, end=end, type=self._type)

    def get_alpha_monthly(self, start: dt.date, end: dt.date) -> pl.DataFrame:
        return alpha_monthly(start=start, end=end, type=self._type)
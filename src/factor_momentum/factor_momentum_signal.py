import datetime as dt
import polars as pl

from ._wrappers import factorspace_signals_monthly, assetspace_signal_monthly, alpha_monthly

class FactorMomentumSignal:
    def __init__(self, type: str):
        self._type = type

    def get_factorspace_signal(self, start: dt.date, end: dt.date) -> pl.DataFrame:
        return factorspace_signals_monthly(start=start, end=end, type=self._type)
    
    def get_signal(self, start: dt.date, end: dt.date) -> pl.DataFrame:
        return assetspace_signal_monthly(start=start, end=end, type=self._type)

    def get_alpha(self, start: dt.date, end: dt.date) -> pl.DataFrame:
        return alpha_monthly(start=start, end=end, type=self._type)
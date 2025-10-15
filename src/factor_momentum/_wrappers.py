import polars as pl
import datetime as dt

from ._loaders import _scan_monthly_factor_returns, _load_monthly_asset_data
from ._factor_signal_construction import construct_factor_signal_monthly
from ._map_signal_to_assets import construct_asset_signal_monthly

#TODO: Docstring

def factorspace_signals_monthly(
        start: dt.date,
        end: dt.date,
        type: str
) -> pl.DataFrame:
    
    return construct_factor_signal_monthly(
        monthly_factor_returns = _scan_monthly_factor_returns(start=start, end=end),
        type=type
    )


def assetspace_signal_monthly(
    start: dt.date,
    end: dt.date,
    type: str
) -> pl.DataFrame:

    return construct_asset_signal_monthly(
        factor_signals_monthly=factorspace_signals_monthly(start=start, end=end, type=type),
        asset_data_monthly=_load_monthly_asset_data(start=start, end=end),
    )
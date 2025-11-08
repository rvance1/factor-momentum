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

def alpha_monthly(
    start: dt.date,
    end: dt.date,
    type: str 
) -> pl.DataFrame:
    
    return (assetspace_signal_monthly(start=start, end=end, type=type)
    .with_columns(
        (pl.col('signal').sub(pl.col('signal').mean().over('month')) / pl.col('signal').std().over('month')).alias('score'),
        pl.col('signal').mul(0).add(0.05).alias('IC'),
        pl.col('specific_risk').mul(0.01)
    )
    .with_columns(
        pl.col('score').mul(pl.col('IC')).mul(pl.col('specific_risk')).alias('alpha')
    )
    .rename({"month": "date"})
    .select(['date', 'barrid', 'alpha'])
    )
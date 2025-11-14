import polars as pl
import datetime as dt
import numpy as np

from sf_quant.data.exposures import load_exposures
from sf_quant.data.assets import load_assets
from sf_quant.data.factors import load_factors

from .PCA import RollingPCA
from ._constants import FACTORS

# TODO: Docstring


def _load_monthly_asset_data (
        start: dt.date, end: dt.date
) -> pl.DataFrame:

    columns = ['date', 'barrid'] + FACTORS

    daily = load_assets(start=start, end=end, columns=['date', 'barrid', 'return', 'market_cap', 'specific_risk'], in_universe=True).join(
        load_exposures(start=start, end=end, columns=columns, in_universe=True),
        on=['barrid', 'date'],
        how='inner'
    ).sort(['barrid', 'date'])

    return (daily.lazy().with_columns(
        pl.col('date').dt.truncate('1mo').alias('month')
    )
    .group_by(['month', 'barrid']).agg(
        [(np.log(1 + pl.col('return')*.01).sum())
        .alias('ret'),
        pl.col('market_cap').last(),
        (np.sqrt(np.pow(pl.col('specific_risk'), 2).mean()))]
        +
        [pl.col(fac).mean() for fac in FACTORS]
    )
    .sort(['barrid', 'month'])
    .collect()
    )


def _scan_monthly_factor_returns (
        start: dt.date, end: dt.date
        ) -> pl.LazyFrame:

    daily = load_factors(start=start, end=end, factors=FACTORS)
    daily = daily.unpivot(index='date', variable_name='factor', value_name='ret')

    return (daily.lazy().with_columns(
        pl.col('date').dt.truncate('1mo').alias('month'),
        pl.col('ret').shift(1).over('factor').alias('lag_ret')
    )
    .group_by(['factor', 'month']).agg(
        (np.log(1 + pl.col('ret')*.01).sum()).alias('ret')
    )
    .sort(['factor', 'month'])
    .with_columns(
        pl.col('ret').shift(1).alias('lag_ret')
    )
    )


def _scan_monthly_pc_returns (
        start: dt.date, end: dt.date, n_compenents: int, lookback_window: int
) -> pl.LazyFrame:
    
    pca_engine = RollingPCA(n_components=n_compenents, lookback_window=lookback_window)
    
    factor_returns = load_factors(start=start, end=end, factors=FACTORS).lazy()

    pcs = pca_engine.fit_transform_rolling_monthly(start, end, factor_returns)

    return (pcs.unpivot(index='date', variable_name='factor', value_name='ret').lazy()
    .with_columns(
        pl.col('date').dt.truncate('1mo').alias('mo'),
    )
    .group_by(['factor', 'mo']).agg(
        pl.col('date').first().alias('month'),
        (np.log(1 + pl.col('ret')*.01).sum()).alias('ret'),
    )
    .sort(['factor', 'month'])
    .with_columns(
        pl.col('ret').shift(1).over('factor').alias('lag_ret')
    )
    .drop('mo')
    )

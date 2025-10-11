import polars as pl
import numpy as np

from sf_quant.data.exposures import load_exposures, get_exposures_columns
from sf_quant.data.factors import get_factor_names
from sf_quant.data.assets import load_assets, get_assets_columns

import sf_quant.data as sfd

import datetime as dt

from factor_singal_construction import construct_factor_signal


FACTORS = [fac for fac in get_factor_names('style') if not fac in ['USSLOWL_MOMENTUM','USSLOWL_LTREVRSL']]


def _prep_monthly (
        start: dt.date, end: dt.date
) -> pl.LazyFrame:

    columns = ['date', 'barrid'] + FACTORS

    daily = load_assets(start=start, end=end, columns=['date', 'barrid', 'return', 'market_cap'], in_universe=True).join(
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
        pl.col('market_cap').last()]
        +
        [pl.col({fac}).mean() for fac in FACTORS]
    )
    .sort(['barrid', 'month'])
    )

def construct_mapped_signal (
        start: dt.date, end: dt.date, type: str
) -> pl.DataFrame:
    
    monthly = _prep_monthly(start=start, end=end).collect()

    factor_signals = (construct_factor_signal(start=start, end=end, type=type)
                      .pivot(on='factor', index='month', values='signal'))
    
    merged = monthly.join(factor_signals, on='month', how='left', suffix='_signal')

    prods = merged.with_columns(merged.columns)
    for fac in FACTORS:
        prods = prods.with_columns(
            (pl.col(fac) * pl.col(f'{fac}_signal')).alias(f'{fac}_signal_exposure')
        ).drop([fac, f'{fac}_signal'])

    prods = prods.drop_nulls()

    return (prods.select(
        pl.col('month'),
        pl.col('barrid'),
        pl.col('ret'),
        pl.col('market_cap'),
        prods[:, 4:18].sum_horizontal().alias('signal')
    )
    .sort(['barrid', 'month'])
    )
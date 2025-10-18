import polars as pl
import datetime as dt

from ._constants import FACTORS

#TODO: require columns for each df, docstring


def construct_asset_signal_monthly (
        factor_signals_monthly: pl.DataFrame,
        asset_data_monthly: pl.DataFrame,
) -> pl.DataFrame:

    factor_signals_monthly_wide = (factor_signals_monthly.pivot(on='factor', index='month', values='signal'))
    
    print("DEBUG: Merging....")
    merged = asset_data_monthly.join(factor_signals_monthly_wide, on='month', how='left', suffix='_signal')

    print("DEBUG: Mapping....")
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
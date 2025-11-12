import polars as pl
import numpy as np

from ._constants import TYPES

#TODO: require columns for each df, docstring

def construct_factor_signal_monthly (
        monthly_factor_returns: pl.LazyFrame, type: str 
) -> pl.DataFrame:

    if type not in TYPES:
            raise ValueError(
                f"Invalid type '{type}'. Must be one of these:  {', '.join(TYPES)}"
            )
    
    
    if type == "1m cross-section":
        return (monthly_factor_returns.with_columns(
            pl.col("lag_ret").rank('dense').over('month').alias('rank'),
            pl.col('lag_ret').count().over('month').alias('count')
        )
        .with_columns(
            pl.when(pl.col('rank') < pl.col('count')*0.5+0.5)
            .then(-1)
            .when(pl.col('rank') > pl.col('count')*0.5+0.5)
            .then(1)
            .otherwise(0)
            .alias('signal')
        )
        .collect()
        )
    
    elif type == "12m time-series continuous":
        return (monthly_factor_returns.with_columns(
            (pl.col('lag_ret'))
            .shift(1)
            .rolling_sum(11)
            .over('factor')
            .alias('signal')
        )
        .drop_nulls()
        .collect()
        )
    
    elif type == "12m time-series discrete":
        return (monthly_factor_returns.with_columns(
            (pl.col('lag_ret'))
            .shift(1)
            .rolling_sum(11)
            .over('factor')
            .alias('signal')
        )
        .with_columns(
            (pl.col('signal') / pl.col('signal').abs()).alias('signal')
        )
        .drop_nulls()
        .collect()
        )
    
    else:
        raise NotImplementedError(f"Missing type: {type!r}.")
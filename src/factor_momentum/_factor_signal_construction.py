import polars as pl
import numpy as np

#TODO: require columns for each df, docstring

def construct_factor_signal_monthly (
        monthly_factor_returns: pl.LazyFrame, type: str 
) -> pl.DataFrame:

    if type == "cross section":
        return (monthly_factor_returns.with_columns(
            pl.col("lag_ret").rank('dense').over('month').alias('rank'),
            pl.col('lag_ret').count().over('month').alias('count')
        )
        .with_columns(
            pl.when(pl.col('rank') <= pl.col('count')*0.5)
            .then(-1)
            .otherwise(1)
            .alias('signal')
        )
        .collect()
        )
    
    elif type == "rolling continuous":
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
    
    elif type == "rolling discrete":
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
        raise ValueError(f"Invalid type: {type!r}. Must be 'cross section', 'rolling continuous', or 'rolling discrete'.")
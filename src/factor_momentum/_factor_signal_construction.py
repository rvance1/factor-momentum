import polars as pl
import numpy as np

#TODO: require columns for each df, docstring

def construct_factor_signal_monthly (
        monthly_factor_returns: pl.LazyFrame, type: str 
) -> pl.DataFrame:

    if type == "discrete":
        return (monthly_factor_returns.with_columns(
            pl.col("lag_ret").rank('dense').over('month').alias('rank'),
            pl.col('lag_ret').count().over('month').alias('count')
        )
        .with_columns(
            pl.when(pl.col('rank') < pl.col('count')*0.5)
            .then(-1)
            .otherwise(1)
            .alias('signal')
        )
        .collect()
        )
    
    elif type == "rolling":
        return (monthly_factor_returns.with_columns(
            (np.log(pl.col('lag_ret')*.01+1))
            .shift(2)
            .rolling_sum(10)
            .alias('signal')
        )
        .drop_nulls()
        .collect()
        )
    else:
        raise ValueError(f"Invalid type: {type!r}. Must be 'rolling' or 'discrete'.")
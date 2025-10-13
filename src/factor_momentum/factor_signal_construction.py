from sf_quant.data.factors import load_factors
import polars as pl
import datetime as dt
import numpy as np

from .constants import FACTORS

#TODO: docstring


def _prep_monthly (
        start: dt.date, end: dt.date
        ) -> pl.LazyFrame:

    daily = load_factors(start=start, end=end, factors=FACTORS)
    daily = daily.unpivot(index='date', variable_name='factor', value_name='ret')

    return (daily.lazy().with_columns(
        pl.col('date').dt.truncate('1mo').alias('month')
    )
    .group_by(['factor', 'month']).agg(
        (np.log(1 + pl.col('ret')*.01).sum())
        .alias('ret')
    )
    .sort(['factor', 'month'])
    .with_columns(
        pl.col('ret').shift(1).over('factor').alias('lag_ret')
    )
    )



def construct_factor_signal (
        start: dt.date, end: dt.date, type: str 
) -> pl.DataFrame:
    

    monthly = _prep_monthly(start=start, end=end)

    if type == "discrete":
        return (monthly.with_columns(
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
        return (monthly.with_columns(
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
import polars as pl
import datetime as dt

def get_earnings_season_markers(start: dt.date, end: dt.date) -> pl.DataFrame:
    
    quater_filter: pl.Expr = (
        pl.col("date").dt.ordinal_day().is_between(15, 36)   |  # Jan 15–Feb 5
        pl.col("date").dt.ordinal_day().is_between(105, 125) |  # Apr 15–May 5
        pl.col("date").dt.ordinal_day().is_between(196, 217) |  # Jul 15–Aug 5
        pl.col("date").dt.ordinal_day().is_between(288, 309)    # Oct 15–Nov 5
    )
    
    return (pl.date_range(
        start, end, interval="1d", eager=True
    )
    .to_frame(name="date")
    .with_columns(
        pl.when(quater_filter).then(1).otherwise(0).alias("is_earnings_season")
    )
    )


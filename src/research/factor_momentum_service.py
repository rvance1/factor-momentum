import datetime as dt
import numpy as np
import polars as pl
import dataframely as dy
from typing import TypeAlias
from enum import StrEnum

from factor_momentum import PcaEngine, FACTORS
from sf_quant.data import load_factors

from research.seasons import get_earnings_season_markers

class PCReturnsSchema(dy.Schema):
    factor = dy.String()
    date = dy.Date()
    ret = dy.Float64(nullable=True)
    lag_ret = dy.Float64(nullable=True)

class PCSignalsSchema(dy.Schema):
    factor = dy.String()
    date = dy.Date()
    ret = dy.Float64()
    lag_ret = dy.Float64(nullable=True)
    rank = dy.UInt32()
    signal = dy.Int32()

class PortReturnsSchema(dy.Schema):
    date = dy.Date()
    median = dy.Float64()
    losers = dy.Float64()
    winners = dy.Float64()
    ls = dy.Float64()
    
PCReturnsDf: TypeAlias = dy.DataFrame[PCReturnsSchema]
PCSignalsDf: TypeAlias = dy.DataFrame[PCSignalsSchema]
PortReturnsDf: TypeAlias = dy.DataFrame[PortReturnsSchema]

class Interval(StrEnum):
    DAILY = "1d"
    MONTHLY = "1mo"

class EngineType(StrEnum):
    ROLLING = "rolling"


class FactorMomentumService:

    def __init__(self, start: dt.date, end: dt.date):
        self.start = start
        self.end = end
        self.rolling_engine = None
        self.expanding_engine = None


    def __build_engine(self, n_components: int, lookback_window: int | None = None) -> None:
        
        if lookback_window is None:
            self.expanding_engine = PcaEngine(n_components=n_components, lookback_window=100)
        else:
            self.rolling_engine = PcaEngine(n_components=n_components, lookback_window=lookback_window)


    def __process_monthly(self, df: pl.DataFrame) -> pl.DataFrame:
        return (df.drop('state').unpivot(index='date', variable_name='factor', value_name='ret').lazy()
        .with_columns(
            pl.col('date').dt.truncate('1mo').alias('mo'),
        )
        .group_by(['factor', 'mo']).agg(
            pl.col('date').min().alias('month'),
            pl.col('ret').mul(.01).log1p().sum().alias('ret'),
        )
        .drop('mo')
        .sort(['factor', 'month'])
        .with_columns(
            pl.col('ret').shift(1).over('factor').alias('lag_ret')
        )
        .rename({"month": "date"})
        .collect()
        )


    def __process_daily(self, df: pl.DataFrame) -> pl.DataFrame:
        return (df.drop('state').unpivot(
            index='date', variable_name='factor', value_name='ret'
        )
        .with_columns(
            pl.col("ret").mul(.01).log1p()
        )
        .with_columns(
            pl.col('ret').shift(1).over('factor').alias('lag_ret')
        )
        )
    

    def get_rolling_pcs(self, n_components: int, lookback_window: int, inter: Interval, filter_earnings_season: bool) -> PCReturnsDf:
        """
        Docstring for get_rolling_pcs

        :param n_components: Defines the number of principal components to compute.
        :type n_components: int
        :param lookback_window: Defines the number of past observations to consider when computing the principal components for each date.
        :type lookback_window: int
        :param inter: Defines the frequency of the output data.
        :type inter: Interval
        :param filter_earnings_season: Defines whether to filter out earnings season dates.
        :type filter_earnings_season: bool
        :return: A DataFrame containing the rolling principal components for each date, aggregated to monthly frequency and lagged by one month.
        :rtype: DataFrame
        """
        if self.rolling_engine is None:
            raise ValueError("Rolling PCA engine not built. Please call __build_engine with appropriate parameters before calling this method.")

        
        factor_returns = load_factors(self.start, self.end, FACTORS)

        if filter_earnings_season:
            earnings_flags = get_earnings_season_markers(self.start, self.end)
            factor_returns = factor_returns.join(earnings_flags, on='date', how='left').filter(pl.col('is_earnings_season').eq(0)).drop('is_earnings_season').sort('date').lazy()
        
        factor_returns = factor_returns.sort('date').lazy()
        
        
        if inter == Interval.MONTHLY:
            pc_rolling_returns = self.rolling_engine.fit_transform_rolling_monthly(factor_returns)
            pc_rolling_returns = self.__process_monthly(pc_rolling_returns)
        elif inter == Interval.DAILY:
            pc_rolling_returns = self.rolling_engine.fit_transform_rolling_daily(factor_returns)
            pc_rolling_returns = self.__process_daily(pc_rolling_returns)
        else:
            raise ValueError(f"Invalid interval {inter}")

        print(pc_rolling_returns.collect_schema())
        return PCReturnsSchema.validate(pc_rolling_returns)


    def get_expanding_pcs(self, n_components: int, filter_earnings_season: bool) -> PCReturnsDf:
        """
        Docstring for get_expanding_pcs

        :param n_components: Defines the number of principal components to compute.
        :type n_components: int
        :return: A DataFrame containing the expanding principal components for each date, aggregated to monthly frequency and lagged by one month.
        :rtype: DataFrame
        """
        if self.expanding_engine is None:
            raise ValueError("Expanding PCA engine not built. Please call __build_engine with appropriate parameters before calling this method.")


        factor_returns = load_factors(self.start, self.end, FACTORS)

        if filter_earnings_season:
            earnings_flags = get_earnings_season_markers(self.start, self.end)
            factor_returns = factor_returns.join(earnings_flags, on='date', how='left').filter(pl.col('is_earnings_season').eq(0)).drop('is_earnings_season').sort('date').lazy()
        
        factor_returns = factor_returns.sort('date').lazy()


        pc_rolling_returns = self.expanding_engine.fit_transform_expanding_monthly(self.start, factor_returns)

        return PCReturnsSchema.validate(self.__process_monthly(pc_rolling_returns))


    def build_cross_sectional_signals(self, pc_returns: PCReturnsDf) -> PCSignalsDf:
        """
        Docstring for build_cross_sectional_signals

        :param pc_returns: A DataFrame containing the principal component returns for each date.
        :type pc_returns: PCReturnsDf
        :return: A DataFrame containing the cross-sectional signals for each date, based on the principal components.
        :rtype: DataFrame
        """
        signals = (pc_returns.with_columns(
            pl.col('lag_ret').rank('dense').over('date').alias('rank')
        )
        .with_columns(
            pl.when(pl.col('rank') < 3)
            .then(-1)
            .when(pl.col('rank') > 3)
            .then(1)
            .otherwise(0)
            .alias('signal')
        )
        .drop_nulls()
        )

        return PCSignalsSchema.validate(signals)
    

    def build_portfolios(self, signals: PCSignalsDf) -> PortReturnsDf:
        """
        Docstring for build_portfolios

        :param signals: A DataFrame containing the PC signals for each date.
        :type signals: PCSignalsDf
        :return: A DataFrame containing the portfolio returns for each date, based on the PC signals.
        :rtype: DataFrame
        """
        # This is a placeholder implementation. The actual implementation would depend on the specific portfolio construction methodology you want to use.
        ports = (signals.group_by(['date', 'signal']).agg(
            pl.col('ret').sum()
        )
        .sort('date')
        .pivot(on='signal', index='date')
        .with_columns(
            (pl.col('1') - pl.col('-1')).alias('ls')
        )
        .rename({
            '-1': 'losers',
            '0': 'median',
            '1': 'winners'
        })
        )

        return PortReturnsSchema.validate(ports)
    

    def run_expanding_pipeline(self, n_components: int, filter_earnings_season: bool = False) -> tuple[PortReturnsDf, PCSignalsDf, PCReturnsDf]:
        
        self.__build_engine(n_components=n_components, lookback_window=None)

        pc_returns = self.get_expanding_pcs(n_components, filter_earnings_season)
        signals = self.build_cross_sectional_signals(pc_returns)
        ports = self.build_portfolios(signals)

        return ports, signals, pc_returns


    def run_rolling_pipeline(self, n_components: int, lookback_window: int, interval: Interval, filter_earnings_season: bool = False) -> tuple[PortReturnsDf, PCSignalsDf, PCReturnsDf]:
        
        self.__build_engine(n_components=n_components, lookback_window=lookback_window)
        
        pc_returns = self.get_rolling_pcs(n_components, lookback_window, interval, filter_earnings_season)
        signals = self.build_cross_sectional_signals(pc_returns)
        ports = self.build_portfolios(signals)

        return ports, signals, pc_returns
    

    def extract_loadings_dict(self, engine_type="rolling", pc: int | None = None) -> dict[str, np.ndarray]:
        """
        Docstring for extract_loadings

        :param engine_type: Specifies which PCA engine to extract loadings from. Must be either "rolling" or "expanding". Defaults to "rolling".
        :type engine_type: str, optional
        :return: A dictionary where the keys are the dates corresponding to each PCA fit, and the values are the loading matrices (as numpy arrays) for the principal components at those dates.
        """

        if engine_type not in ["rolling", "expanding"]:
            raise ValueError("Invalid engine_type. Must be either 'rolling' or 'expanding'.")
        
        if engine_type == "rolling":
            if self.rolling_engine is None:
                raise ValueError("Rolling PCA engine not built. Please call __build_engine with appropriate parameters before calling this method.")
            engine = self.rolling_engine
            states = self.rolling_engine.states
        else:
            if self.expanding_engine is None:
                raise ValueError("Expanding PCA engine not built. Please call __build_engine with appropriate parameters before calling this method.")
            engine = self.expanding_engine
            states = self.expanding_engine.states

        if pc is not None:
            if pc > engine.n_components - 1:
                raise ValueError(f"Requested PC {pc} exceeds the number of components in the engine ({engine.n_components}).")
            
            return {key: states[key]['components'][pc] for key in states.keys() if states[key]}
        
        
        return {key: states[key]['components'] for key in states.keys()}
    

    def extract_loadings_df_for_pc(self, engine_type="rolling", pc: int = 0) -> pl.DataFrame:
        """
        Docstring for extract_loadings_df_for_pc

        :param engine_type: Specifies which PCA engine to extract loadings from. Must be either "rolling" or "expanding". Defaults to "rolling".
        :type engine_type: str, optional
        :param pc: Specifies which principal component's loadings to extract. Must be a non-negative integer less than the number of components in the engine. Defaults to 0.
        :type pc: int, optional
        :return: A DataFrame containing the loadings for the specified principal component across all dates in the PCA engine's states.
        """
        loadings_dict = self.extract_loadings_dict(engine_type=engine_type, pc=pc)
        
        return (pl.DataFrame(
            [
                {"date": k, **{f"{FACTORS[i][8:].lower()}": v[i] for i in range(len(v))}}
                for k, v in loadings_dict.items()
            ]
        )
        .sort("date")
        )
    

    def overwrite_pc_loadings_by_df(self, df: pl.DataFrame) -> None:
        pass
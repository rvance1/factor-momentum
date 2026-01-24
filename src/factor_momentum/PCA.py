import polars as pl
import numpy as np
import datetime as dt

from tqdm import tqdm

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

#TODO: Docstring


class PcaEngine:
    def __init__(self, n_components: int, lookback_window: int):
        self.pca_model = PCA(n_components=n_components)
        self.n_components = n_components
        self.scaler = StandardScaler()
        self.lookback = lookback_window
        self.states = {}

    
    def fit_stretch_for_date(
            self, date: dt.date, start_date: dt.date, returns: pl.LazyFrame
            ) -> None:
        """
        Fit the PCA model for a specific reference date using all
        past returns up to that date.
        """
        
        window = (
            returns.filter(
                pl.col('date').is_between(start_date, date, "left")
            )
            .sort('date')
            .drop('date')
            .collect()
            .to_numpy()
        )

        X = self.scaler.fit_transform(window)
        self.pca_model.fit(X)

        self.states[date] = {
            "mean": self.scaler.mean_,
            "scale": self.scaler.scale_,
            "components": self.pca_model.components_,
            "explained_var": self.pca_model.explained_variance_ratio_,
        }

    #TODO: handle not enough lookback data
    def fit_lookback_for_date(
            self, date: dt.date, returns: pl.LazyFrame
            ) -> None:
        """
        Fit the PCA model for a specific reference date using a 
        lookback window of past returns.
        """
        
        window = (
            returns.filter(
                pl.col('date').is_between(date-dt.timedelta(days=self.lookback), date, "left")
            )
            .sort('date')
            .drop('date')
            .collect()
            .to_numpy()
        )

        X = self.scaler.fit_transform(window)
        self.pca_model.fit(X)

        self.states[date] = {
            "mean": self.scaler.mean_,
            "scale": self.scaler.scale_,
            "components": self.pca_model.components_,
            "explained_var": self.pca_model.explained_variance_ratio_,
        }


    def transform_for_date(
            self, date: dt.date, returns: pl.LazyFrame
            ) -> np.ndarray:
        """
        Transform returns on a given date using the PCA
        fitted at that date. Assumes PCA state exists for that date.
        """

        if date not in self.states:
            raise ValueError(f"No PCA state stored for date {date}")
        
        state = self.states[date]

        row = (
            returns.filter(
                pl.col('date').eq(date)
            )
            .drop('date')
            .collect()
        )

        if row.height != 1:
            raise ValueError(f"Expected exactly one row for date {date}, got {row.height}")
        
        x = row.to_numpy().reshape(1, -1)
        
        x_scaled = (x-state['mean']) / state['scale']

        return x_scaled @ state['components'].T


    def transform_chunk(
            self, state_date: dt.date, returns_chunk: pl.LazyFrame
            ) -> pl.DataFrame:
        """
        Transform all given returns using the PCA fitted for the 
        specified date. Assumes PCA state exists for that date.
        """

        if state_date not in self.states:
            raise ValueError(f"No PCA state stored for date {state_date}")
        
        state = self.states[state_date]

        window = (
            returns_chunk
            .collect()
        )

        if window.height == 0:
            raise ValueError(
                f"Expected at least 1 row, got {window.height}"
            )
        
        X = window.drop('date').to_numpy()
        
        X_scaled = (X - state["mean"]) / state["scale"]
        PCs = X_scaled @ state["components"].T

        pc_cols = {f"pc{i}": PCs[:, i] for i in range(self.n_components)}

        return window.select("date").with_columns(**pc_cols)


    def fit_transform_rolling_monthly(
            self, returns: pl.LazyFrame
    ) -> pl.DataFrame:
        
        returns_monthly = (
            returns
            .with_columns(pl.col('date').dt.truncate('1mo').alias('month'))
            .group_by('month')
            .agg(pl.col('date').first())
            .sort('date')
        )

        dates = (
            returns_monthly
            .drop('month')
            .collect()
        )['date'].to_list()


        print("Fitting rolling PCA...")
        for date in tqdm(dates[1:], desc="Rolling PCA"):
            self.fit_lookback_for_date(date, returns)
        
        print("Transforming rolling PCA...")
        pcs = []
        for date in tqdm(dates[1:], desc="Rolling PCA"):            
            
            chunk = (
                returns
                .with_columns(pl.col('date').dt.truncate('1mo').alias('month'))
                .filter(pl.col('month').eq(date.replace(day=1)))
                .drop('month')
                .sort('date')
            )
            
            pcs.append(
                self.transform_chunk(date, chunk)
                .with_columns(
                    pl.lit(date).alias('state')
                )
            )
        
        return pl.concat(pcs, how="vertical")


    def fit_transform_expanding_monthly(
                self, start_date: dt.date, returns: pl.LazyFrame
        ) -> pl.DataFrame:
            
            returns_monthly = (
                returns
                .with_columns(pl.col('date').dt.truncate('1mo').alias('month'))
                .group_by('month')
                .agg(pl.col('date').first())
                .sort('date')
            )

            dates = (
                returns_monthly
                .drop('month')
                .collect()
            )['date'].to_list()


            print("Fitting expanding PCA...")
            for date in tqdm(dates[1:], desc="Expanding PCA"):
                self.fit_stretch_for_date(date, start_date, returns)
            
            print("Transforming expanding PCA...")
            pcs = []
            for date in tqdm(dates[1:], desc="Expanding PCA"):            
                
                chunk = (
                    returns
                    .with_columns(pl.col('date').dt.truncate('1mo').alias('month'))
                    .filter(pl.col('month').eq(date.replace(day=1)))
                    .drop('month')
                    .sort('date')
                )
                
                pcs.append(
                    self.transform_chunk(date, chunk)
                    .with_columns(
                        pl.lit(date).alias('state')
                    )
                )
            
            return pl.concat(pcs, how="vertical")


    def inverse_transform_chunk(
            self, state_date: dt.date, returns_chunk: pl.LazyFrame
            ) -> pl.DataFrame:
        
        if state_date not in self.states:
            raise ValueError(f"No PCA state stored for date {state_date}")
        
        state = self.states[state_date]

        window = (
            returns_chunk
            .collect()
        )

        if window.height == 0:
            raise ValueError(
                f"Expected at least 1 row, got {window.height}"
            )
        
        X = window.drop('date').to_numpy()
        
        X_scaled = (X - state["mean"]) / state["scale"]
        PCs = X_scaled @ state["components"].T

        pc_cols = {f"pc{i}": PCs[:, i] for i in range(self.n_components)}

        return window.select("date").with_columns(**pc_cols)
        
        
        # L = pca_engine.pca_model.components_
        # pc_weights = [1,0,1,-1,-1]
        # factor_weights = pc_weights @ L
        
        pass
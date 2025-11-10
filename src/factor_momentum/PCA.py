import polars as pl
import numpy as np
import datetime as dt

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler



class RollingPCA:
    def __init__(self, n_components: int, window: int):
        self.pca_model = PCA(n_components=n_components)
        self.scalar = StandardScaler()
        self.window = window

        self.pca_loadings_matricies = {}
    
    def _fit_to_dates(
            self, start: dt.date, end:dt.date, store_date: dt.date, factor_returns: pl.LazyFrame
            ) -> None:
        
        window = (
            factor_returns
            .filter(pl.col('date').is_between(start, end, 'both'))
            .drop('date')
            .collect()
            )

        X = self.scalar.fit_transform(window)
        self.pca_model.fit(X)

        self.pca_loadings_matricies[store_date] = self.pca_model.components_


    def _transform_date(self, date: dt.date, factor_returns: pl.LazyFrame) -> pl.DataFrame:
        date_returns = (
            factor_returns
            .filter(pl.col('date').eq(date))
            .drop('date')
            .collect()
        )

        pc_returns = (
            pl.DataFrame(
                self.pca_model.transform(date_returns.to_numpy())
            )
            .with_columns(
                pl.lit(date)
            )
        )

        return pc_returns


    def fit_transform_rolling(
            start: dt.date, end: dt.date, window: int
    ) -> pl.DataFrame:
        pass

    def get_factor_weights_from_date(date: dt.date) -> np.ndarray[float]:
        
        # L = pca_engine.pca_model.components_
        # pc_weights = [1,0,1,-1,-1]
        # factor_weights = pc_weights @ L
        
        
        pass
import polars as pl
import numpy as np
import datetime as dt

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from sf_quant.data import load_factors
from ._constants import FACTORS

_scalar = StandardScaler()

def _fit_to_month():
    pass

def _transform_month():
    pass

def fit_transform_rolling(
        start: dt.date, end: dt.date
) -> pl.DataFrame:
    pass
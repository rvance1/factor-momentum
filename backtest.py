#!/usr/bin/env python
import datetime as dt
from factor_momentum import FactorMomentumSignal

import sf_quant.backtester as sfb
import sf_quant.optimizer as sfo

from dotenv import load_dotenv
import os

load_dotenv()
write_out = os.getenv('TMP')

def main():
    
    constraints = [
        sfo.FullInvestment(),
        sfo.LongOnly(),
        sfo.NoBuyingOnMargin(),
        sfo.UnitBeta()
    ]

    start, end = dt.date(2001,1,1), dt.date(2020,1,1)
    
    signal = FactorMomentumSignal(type="cross section")
    
    weights = sfb.backtest_parallel(
        signal.get_alpha_monthly(start=start, end=end),
        constraints=constraints,
        gamma=2,
        n_cpus=4
        )
    
    weights.write_parquet(f'{write_out}/fm_weights.parquet')


if __name__ == "__main__":
    main()
    
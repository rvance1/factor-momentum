import pandas as pd
import numpy as np
from collections import namedtuple
from tabulate import tabulate
import statsmodels.formula.api as smf


def qtrdt(date):
    delta = ((date.dt.month.values - 1) // 3 + 1)*3 - 1
    base = date.values.astype('datetime64[Y]').astype('datetime64[M]')
    return (base.astype(int) + delta).astype('datetime64[M]')


def summary(df):
    """
    Computes summary statistics for the columns of a numeric dataframe with 
    a datetime index.

    The summary stats are mean, standard deviation, and the t-statistics of 
    mean = 0.  The typical case is a dataframe where the columns are 
    portfolio returns.

    Parameters
    ----------
    df : a dataframe with numeric data and a datetime index.

    Returns
    -------
    table : namedtuple('table',['header','table'])
        Header is a string header for the summary stats that includes the 
        date range. 

        Table is a dataframe with the summary stats.
    """
    
    s = (df.agg(['mean','std',lambda x: x.mean()/(x.std()/np.sqrt(x.count()))])
         .rename(index={'<lambda>':'tstat'}))

    table = namedtuple('table', ['header','table'])
    header = ("\n\nSummary Statistics\nSample Period: {}-{}\n"
              .format(df.index[0].strftime('%Y:%m'),
                      df.index[-1].strftime('%Y:%m')))
    
    return table(header,s)


def _stack(r,stat,stars,bfmt,sfmt):
    est = 'bstar' if stars else 'b'

    b = r.params.apply(lambda x: '{:{fmt}}'.format(x,fmt=bfmt))
    se = r.bse.apply(lambda x: '({:{fmt}})'.format(x,fmt=sfmt))
    tstat = r.tvalues.apply(lambda x: '({:{fmt}})'.format(x,fmt=sfmt))
    pvalues = r.pvalues.apply(lambda x: '({:{fmt}})'.format(x,fmt=sfmt))        
    bstar = pd.cut(r.pvalues,[-0.01,0.01,0.05,1.01],labels=['***','**',''])
    bstar = b + bstar.astype(str)
    
    return (pd.concat([b,se,tstat,pvalues,bstar],axis=1)
            .rename(columns={0:'b',1:'se',2:'tstat',3:'pvalues',4:'bstar'})
            [[est,stat]].stack())


def regtable(lm,stat='tstat',stars=False,bfmt='.3f',sfmt='.2f'):
    """
    Combines a list of statsmodels regression results in a single table.
    
    regtable stacks the results from each regression  into a single column. 
    T-statistics in parentheses (by default) are interleaved below the
    estimated coefficient. The number of observation and r-square of the
    each regression are also appended.

    Parameters
    ----------
    lm    : a list of statmodels results objects.
    stat  : {'tstat','se','pvalues'}, default is 'tstat'
        Determines whether t-stats, standard errors, or p-values are reported.
    stars : boolean, default False
        if True, significance stars at the 1% (***) and the 5% (**) level are 
        added to the table 
    bmft  : string, default = '.3f'
        Float formatting string for the estimated coefficients
    smft  : string, default = '.2f'
        Float formatting string for the stat paramater (e.g., t-statistics or 
        standard errors)

    Returns
    -------
    out : DataFrame 
        A columnar table where each column corresponds to the results of a
        estimated regression model from statsmodels.

    Examples
    --------
    Suppose ew contains excess portfolio returns, p0 is one of the portfolio
    columns, and ew also contains the Fama-French factors and a momentum 
    factor. In the example below we run a three different factor model 
    regressions and collect the results into a table using regtable. The
    example makes use of the tabulate package to format the regtable dataframe
    for printing.

    >>> r0 = smf.ols('p0 ~ exmkt',data=ew).fit()
    >>> r1 = smf.ols('p0 ~ exmkt + smb + hml',data=ew).fit()
    >>> r2 = smf.ols('p0 ~ exmkt + smb + hml + umd',data=ew).fit()
    >>>
    >>> tabulate(regtable([r0,r1,r2]),headers='keys',tablefmt='simple')

               p0       p0       p0
    ---------  -------  -------  -------
    Intercept  0.352    0.317    0.298
               (7.71)   (7.22)   (6.61)
    exmkt      0.677    0.646    0.650
               (79.80)  (73.61)  (71.78)
    hml                 0.102    0.111
                        (7.93)   (8.06)
    smb                 0.079    0.080
                        (5.51)   (5.56)
    umd                          0.019
                                 (1.82)
    Obs        1098     1098     1098
    RSQ        0.85     0.87     0.87
    """
    
    cols = [x.model.endog_names for x in lm]    
    res = [_stack(r,stat,stars,bfmt,sfmt) for r in lm]

    out = pd.concat(res,axis=1,keys=cols).reset_index()
    out.loc[out['level_1'] == stat,'level_0'] = ''
    out = out.drop('level_1',axis=1).set_index('level_0')
    out.index.name = ""

    obs = pd.DataFrame([int(r.nobs) for r in lm],index=cols,columns=['obs']).T
    rsq = pd.DataFrame(['{:{fmt}}'.format(r.rsquared,fmt=sfmt) for r in lm],
                       index=cols,columns=['Rsq']).T

    return pd.concat([out,obs,rsq],axis=0).fillna('')

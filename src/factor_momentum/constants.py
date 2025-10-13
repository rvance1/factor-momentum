from sf_quant.data.factors import get_factor_names


FACTORS = [fac for fac in get_factor_names('style')
            if not fac in ['USSLOWL_MOMENTUM','USSLOWL_LTREVRSL']]
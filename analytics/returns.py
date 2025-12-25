import pandas as pd

def absolute_return(start_price: float, end_price: float) -> float:
    return (end_price / start_price) - 1


def cagr(start_price: float, end_price: float, years: float) -> float:
    return (end_price / start_price) ** (1 / years) - 1

import pandas as pd

def load_index_prices_from_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return df

import pandas as pd

# adjust path if needed
price_history = pd.read_parquet("data/processed/price_history.parquet")
entity_master = pd.read_parquet("data/processed/entity_master.parquet")

print("PRICE HISTORY COLUMNS")
print(price_history.columns.tolist())
print("\nPRICE HISTORY HEAD")
print(price_history.head())

print("\n" + "-"*60 + "\n")

print("ENTITY MASTER COLUMNS")
print(entity_master.columns.tolist())
print("\nENTITY MASTER HEAD")
print(entity_master.head())

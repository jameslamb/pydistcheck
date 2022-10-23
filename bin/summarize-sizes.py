import sys

import pandas as pd

CSV_FILE = sys.argv[1]

df = pd.read_csv(CSV_FILE)
df["size_bytes"] = df["size"]
df["size_pct"] = df["size_bytes"] / df["size_bytes"].sum()

pd.set_option("display.max_rows", 200)
print(df.sort_values(["size_bytes"], ascending=False))

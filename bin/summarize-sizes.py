import sys
import pandas as pd
import numpy as np

CSV_FILE = sys.argv[1]


def _size_string_to_bytes(size_str: str) -> float:
    _UNIT_TO_NUM_BYTES = {
        "B": 1,
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
        "T": 1024**4,
    }
    # some flavors of `du` return "0" instead of "0B" for empty files
    if size_str == "0":
        return 0
    unit_str = size_str[-1:]
    num = float(size_str[:-1])
    return num * _UNIT_TO_NUM_BYTES[unit_str]


df = pd.read_csv(CSV_FILE)
df["size_bytes"] = df["size"].apply(lambda x: _size_string_to_bytes(x))
df["size_pct"] = df["size_bytes"] / df["size_bytes"].sum()

pd.set_option("display.max_rows", 200)
print(df.sort_values(["size_bytes"], ascending=False))

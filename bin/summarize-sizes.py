import sys
import pandas as pd

CSV_FILE = sys.argv[1]


def _size_string_to_bytes(size_str: str) -> float:
    _UNIT_TO_NUM_BYTES = {
        "B": 1,
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
        "T": 1024**4,
    }
    unit_str = size_str[-1:]
    num = float(size_str[:-1])
    return num * _UNIT_TO_NUM_BYTES[unit_str]


df = pd.read_csv(CSV_FILE)
df["size_bytes"] = df["size"].apply(lambda x: _size_string_to_bytes(x))

pd.set_option("display.max_rows", 200)
print(df.sort_values(["size_bytes"], ascending=False))

#!/usr/bin/env python

"""
Ugh this is so gross.

Ok so basically, if you run ``find ... -exec du -ch ...``
over a LOT of files, it can return multiple "total" lines, like

```text
 70M    total
204K    total
```

There are some fixes mentioned in https://stackoverflow.com/questions/1323696/why-does-find-name-txt-xargs-du-hc-give-multiple-totals,
but they seem to not be portable between GNU du and the Mac one.

So this script just takes in multiple such lines like that and
returns a single sum.

It uses ``sys.stdin`` so it can be part of a pipe.
"""

import sys

_UNIT_TO_NUM_BYTES = {
    "B": 1,
    "K": 1024,
    "M": 1024**2,
    "G": 1024**3,
    "T": 1024**4,
}

total_bytes = 0.0

lines = []
for line in sys.stdin:
    size_str = line.replace("total", "").strip()
    # some flavors of `du` return "0" instead of "0B" for empty files
    if size_str == "0":
        continue
    unit_str = size_str[-1:]
    count_float = float(size_str[:-1])
    total_bytes += count_float * _UNIT_TO_NUM_BYTES[unit_str]

bytes_in_gb = _UNIT_TO_NUM_BYTES["G"]
if total_bytes >= bytes_in_gb:
    print(f"{round(total_bytes / bytes_in_gb, 1)}G")
else:
    print(f"{round(total_bytes / 1024**2, 1)}M")

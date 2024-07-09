"""Benchmark v0.6.0-csv plot."""

import matplotlib.pyplot as plt
import pandas as pd

bench = pd.read_csv(
    "./scripts/benchmark-v0.6.0-csv.csv", header=0, sep=";", encoding="utf-8"
)
bench.plot(
    x="# rows",
    subplots=[
        ("v0.5.0", "Pandas (1000)", "Pandas (5000)", "Pandas (10000)"),
        ("Ratio (1000)", "Ratio (5000)", "Ratio (10000)"),
    ],
    sharex=True,
)
plt.savefig("./scripts/benchmark-v0.6.0-csv.png")

# %%
import os
from glob import glob
from typing import Dict

import matplotlib.pyplot as plt

from porter_bench.DataHandler import DataHandler
from porter_bench.MemoryBenchmarker import MemoryPlotter
from porter_bench.TimeBenchmarker import TimePlotter
from porter_bench.utils import load_record

os.chdir(os.path.dirname(os.path.abspath(__file__)))

record_dict = {}
paths = glob("TICTOC_PERFORMANCE/*")

for path in paths:
    record_dict[os.path.basename(path)] = load_record(path, only_latest=False)

datahandler = DataHandler(record_dict)
# %%
plt.figure(figsize=(20, 10))
datahandler.plot_memory_usage(record_name="test")
# %%
datahandler.make_bars(record_name="test")
# %%
plt.figure(figsize=(20, 10))
datahandler.plot_crono(record_name="test")
# %%
name = list(record_dict.keys())[0]
record_name = "test"
record_dict[name]["calls"][record_name]

# %%

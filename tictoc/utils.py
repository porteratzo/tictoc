import os
from glob import glob
import json
from datetime import datetime
import pandas as pd

APPENDED_STEP_DATA_NAME = "_STEP_DICT_DATA"
APPENDED_SUMMARY_NAME = "_STEP_DICT_SUMMARY"
APPENDED_DIR_NAME = "TICTOC_PERFORMANCE"


def load_raw_stepdict_data(path):
    data_dict = {}
    dir_path = os.path.join(path, f"*{APPENDED_STEP_DATA_NAME}.json")
    for col in glob(dir_path, recursive=True):
        with open(col, "r") as json_file:
            data = json.load(json_file)
            base_name = os.path.basename(col).replace(APPENDED_STEP_DATA_NAME + ".json", "")
            data_dict[base_name] = data
    return data_dict


def load_raw_summary_data(record_path):
    data_dict = {}
    dir_path = os.path.join(record_path, f"*{APPENDED_SUMMARY_NAME}.json")
    for col in glob(dir_path, recursive=True):
        with open(col, "r") as json_file:
            data = json.load(json_file)
            base_name = os.path.basename(col).replace(APPENDED_SUMMARY_NAME + ".json", "")
            data_dict[base_name] = data
    return data_dict


def get_latest_record(path):
    files = glob(os.path.join(path, f"{APPENDED_DIR_NAME}", "*"))
    timestamp_format = "%H:%M-%d:%m:%Y"
    sorted_files = sorted(
        files, key=lambda f: datetime.strptime(os.path.basename(f), timestamp_format), reverse=True
    )
    return sorted_files[0]


def get_absolutes(step_dict_data):
    DF_dict = {}
    for benchmark_key in step_dict_data:
        DF_dict[benchmark_key] = pd.DataFrame(
            [step["absolutes"] for step in step_dict_data[benchmark_key]]
        )
    return DF_dict


def get_infos(step_dict_data):
    DF_dict = {}
    for benchmark_key in step_dict_data:
        DF_dict[benchmark_key] = pd.DataFrame(
            [step["info"] for step in step_dict_data[benchmark_key]]
        )
    return DF_dict

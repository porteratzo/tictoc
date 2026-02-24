"""Utility functions for loading and processing benchmark data."""

import json
import os
from datetime import datetime
from glob import glob
from typing import Any

import pandas as pd

APPENDED_STEP_DATA_NAME = "_STEP_DICT_DATA"
APPENDED_MEMORY_NAME = "_MEMORY"
APPENDED_SUMMARY_NAME = "_STEP_DICT_SUMMARY"
APPENDED_DIR_NAME = "TICTOC_PERFORMANCE"


def load_raw_stepdict_data(path: str) -> dict[str, Any]:
    """Load raw step-dict JSON files from a benchmark record directory."""
    data_dict = {}
    dir_path = os.path.join(path, f"*{APPENDED_STEP_DATA_NAME}.json")
    for col in glob(dir_path, recursive=True):
        with open(col, "r") as json_file:
            data = json.load(json_file)
            base_name = os.path.basename(col).replace(
                APPENDED_STEP_DATA_NAME + ".json", ""
            )
            data_dict[base_name] = data
    return data_dict


def load_raw_summary_data(record_path: str) -> dict[str, Any]:
    """Load raw summary JSON files from a benchmark record directory."""
    data_dict = {}
    dir_path = os.path.join(record_path, f"*{APPENDED_SUMMARY_NAME}.json")
    for col in glob(dir_path, recursive=True):
        with open(col, "r") as json_file:
            data = json.load(json_file)
            base_name = os.path.basename(col).replace(
                APPENDED_SUMMARY_NAME + ".json", ""
            )
            data_dict[base_name] = data
    return data_dict


def get_latest_record(path: str) -> str:
    """Return the path of the most recently saved benchmark run."""
    files = glob(os.path.join(path, f"{APPENDED_DIR_NAME}", "*"))
    timestamp_format = "%H:%M-%d:%m:%Y"
    sorted_files = sorted(
        files,
        key=lambda f: datetime.strptime(os.path.basename(f), timestamp_format),
        reverse=True,
    )
    return sorted_files[0]


def get_absolutes(step_dict_data: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Build a DataFrame of per-iteration absolute step times for each benchmark."""
    DF_dict = {}
    for benchmark_key in step_dict_data:
        DF_dict[benchmark_key] = pd.DataFrame(
            [step["absolutes"] for step in step_dict_data[benchmark_key]]
        )
    return DF_dict


def get_calls(step_dict_data: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Build a DataFrame of per-iteration individual call records for each benchmark."""
    DF_dict = {}
    for benchmark_key in step_dict_data:
        DF_dict[benchmark_key] = pd.DataFrame(
            [step["individual_calls"] for step in step_dict_data[benchmark_key]]
        )
    return DF_dict


def get_infos(step_dict_data: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Build a DataFrame of per-iteration info records for each benchmark."""
    DF_dict = {}
    for benchmark_key in step_dict_data:
        DF_dict[benchmark_key] = pd.DataFrame(
            [step["info"] for step in step_dict_data[benchmark_key]]
        )
    return DF_dict


def load_raw_memory_data(path: str) -> dict[str, Any]:
    """Load raw memory JSON files from a benchmark record directory."""
    data_dict = {}
    dir_path = os.path.join(path, f"*{APPENDED_MEMORY_NAME}.json")
    for col in glob(dir_path, recursive=True):
        with open(col, "r") as json_file:
            data = json.load(json_file)
            base_name = os.path.basename(col).replace(
                APPENDED_MEMORY_NAME + ".json", ""
            )
            data_dict[base_name] = data
    return data_dict


def get_data(step_dict_data: dict[str, Any]) -> dict[str, list[Any]]:
    """Extract the raw data list from each benchmark's memory records."""
    DF_dict = {}
    for benchmark_key in step_dict_data:
        DF_dict[benchmark_key] = [
            step["data"] for step in step_dict_data[benchmark_key]
        ]
    return DF_dict


def load_record(record_path: str, only_latest: bool = True) -> dict[str, Any]:
    """Load a benchmark record from disk into a structured dict.

    Args:
        record_path: Path to the benchmark record directory.
        only_latest: If True, load only the most recent run. Defaults to True.

    Returns:
        Dict with keys: summary, absolutes, calls, infos, memory,
        _raw_data, _raw_memory.
    """
    record: dict[str, Any] = {}
    if only_latest:
        record_path = get_latest_record(record_path)
    step_dict_data = load_raw_stepdict_data(record_path)
    memory_data = load_raw_memory_data(record_path)

    record["_raw_data"] = step_dict_data
    record["_raw_memory"] = memory_data
    record["summary"] = load_raw_summary_data(record_path)

    record["memory"] = get_data(memory_data)
    record["absolutes"] = get_absolutes(step_dict_data)
    record["calls"] = get_calls(step_dict_data)
    record["infos"] = get_infos(step_dict_data)
    return record


def find_clusters(
    ordered_crono: list[dict[str, Any]],
    max_length: int,
    cluster_filter: float,
) -> list[dict[str, Any]]:
    """Detect and collapse repeated step sequences in a chronological series."""
    clusters = []
    new_crono = []
    i = 0

    sequence = [i["step_name"] for i in ordered_crono]
    memory_vals = [i["total"] for i in ordered_crono]
    max_memory_usage = max(memory_vals)
    min_memory_usage = min(memory_vals)
    memory_threshold = (max_memory_usage - min_memory_usage) * cluster_filter
    while i < len(sequence):
        # Initialize the current cluster
        current_cluster = sequence[i]
        count = 1

        # Check for repeating sequences up to max_length
        current_memory = ordered_crono[i]["total"]
        memory_spike = False
        match_found = False
        for j in range(0, max_length):
            match_sequence = sequence[i : i + j + 1]
            while (
                i + j < len(sequence)
                and match_sequence == sequence[i + j + 1 : i + j + 2 + j]
                and not memory_spike
            ):
                for timing in ordered_crono[i : i + j + 2 + j]:
                    if abs(timing["total"] - current_memory) > memory_threshold:
                        memory_spike = True
                if not memory_spike:
                    current_cluster = sequence[i : i + j + 1]
                    count += 1
                    i += j + 1
                    match_found = True
        if match_found:
            i += 1

        # Add the cluster to the list
        clusters.append((current_cluster, count))
        partial_crono = ordered_crono[i].copy()
        if count > 1:
            partial_crono["step_name"] = (
                " || ".join(current_cluster) + " x" + str(count)
            )
        new_crono.append(partial_crono)

        # Move to the next character
        i += 1

    return new_crono


def filter_no_change(
    filter_no_change: Any,
    ordered_crono: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Filter out chronological entries where memory did not change significantly."""
    if not isinstance(filter_no_change, float):
        filter_no_change = 0.05
    memory_vals = [i["total"] for i in ordered_crono]
    max_memory_usage = max(memory_vals)
    min_memory_usage = min(memory_vals)
    memory_threshold = (max_memory_usage - min_memory_usage) * filter_no_change
    new_list = [ordered_crono[0]]
    rejected = []
    current_memory = ordered_crono[0]["total"]
    for i in ordered_crono[1:]:
        if abs(i["total"] - current_memory) > memory_threshold:
            new_list.append(i)
            current_memory = i["total"]
        else:
            rejected.append(i)
    ordered_crono = new_list
    return ordered_crono, rejected

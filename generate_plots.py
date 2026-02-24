"""Load benchmark records from example.py and generate all plots."""

import argparse
import os
from typing import Any

import matplotlib.pyplot as plt

from porter_bench.DataHandler import DataHandler
from porter_bench.utils import load_record


def get_record_names(record: dict[str, Any]) -> list[str]:
    """Return the benchmarker names present in the loaded record."""
    return list(record["absolutes"].keys())


def generate_plots(
    record_path: str = ".",
    output_dir: str = "PLOTS",
    show: bool = False,
) -> None:
    """Load benchmark records and generate all plots, saving them to output_dir."""
    print(f"Loading latest record from: {os.path.abspath(record_path)}")
    record = load_record(record_path)

    record_names = get_record_names(record)
    print(f"Found benchmarkers: {record_names}")

    os.makedirs(output_dir, exist_ok=True)

    # DataHandler expects {run_label: record} — one entry per run being compared
    handler = DataHandler({"run": record})

    for record_name in record_names:
        print(f"\n--- Plotting '{record_name}' ---")

        # 1. Time series (absolutes per iteration)
        plt.figure(figsize=(14, 5))
        plt.title(f"{record_name} — time series")
        handler.plot_times(record_name=record_name)
        plt.tight_layout()
        out = os.path.join(output_dir, f"{record_name}_times.png")
        plt.savefig(out, dpi=150)
        print(f"  Saved: {out}")
        if show:
            plt.show()
        plt.close()

        # 2. Bar charts (mean / quantile-filtered mean per step)
        handler.make_bars(record_name=record_name)
        out = os.path.join(output_dir, f"{record_name}_bars.png")
        plt.savefig(out, dpi=150)
        print(f"  Saved: {out}")
        if show:
            plt.show()
        plt.close()

        # 3. Chronological call plot
        plt.figure(figsize=(16, 5))
        plt.title(f"{record_name} — chronological calls")
        handler.plot_crono(record_name=record_name)
        plt.tight_layout()
        out = os.path.join(output_dir, f"{record_name}_crono.png")
        plt.savefig(out, dpi=150)
        print(f"  Saved: {out}")
        if show:
            plt.show()
        plt.close()

        # 4. Memory usage (only if memory data is present)
        mem_data = record["memory"].get(record_name)
        if mem_data and len(mem_data) > 0:
            plt.figure(figsize=(16, 5))
            handler.plot_memory_usage(record_name=record_name)
            plt.tight_layout()
            out = os.path.join(output_dir, f"{record_name}_memory.png")
            plt.savefig(out, dpi=150)
            print(f"  Saved: {out}")
            if show:
                plt.show()
            plt.close()

            # 5. CUDA memory usage (skipped silently if no CUDA data)
            plt.figure(figsize=(16, 5))
            handler.plot_cuda_memory(record_name=record_name)
            if plt.gca().has_data():
                plt.tight_layout()
                out = os.path.join(output_dir, f"{record_name}_cuda_memory.png")
                # plt.savefig(out, dpi=150)
                print(f"  Saved: {out}")
                if show:
                    plt.show()
            else:
                print("  Skipping CUDA memory plot (no CUDA data)")
            plt.close()
        else:
            print("  Skipping memory plots (no memory data)")

    print(f"\nAll plots saved to: {os.path.abspath(output_dir)}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate all plots from porter_bench records."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Root directory containing TICTOC_PERFORMANCE/ (default: current dir)",
    )
    parser.add_argument(
        "--output",
        default="PLOTS",
        help="Directory to save plots (default: PLOTS/)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show plots interactively in addition to saving",
    )
    args = parser.parse_args()
    generate_plots(record_path=args.path, output_dir=args.output, show=args.show)

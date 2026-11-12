"""Alternating GC on/off runs of the end-to-end benchmark; prints medians.

Each run is a separate process (BENCH_GC env var is inherited by the spawned
consumer). Results are single-machine, noisy, and for engine-only/consumer
metrics only; this does not prove an end-to-end improvement.
"""
import os
import re
import statistics
import subprocess
import sys

ROUNDS = int(os.environ.get("GC_ROUNDS", "10"))
PATTERNS = {
    "throughput": r"Consumer-window throughput: ([\d.]+)",
    "engine_median_us": r"engine_only: min [\d.]+ us \| median ([\d.]+)",
    "engine_p99_us": r"engine_only: .*?p99 ([\d.]+) us",
    "engine_p999_us": r"engine_only: .*?p99\.9 ([\d.]+) us",
    "get_median_us": r"get_only: min [\d.]+ us \| median ([\d.]+)",
}


def run_once(mode):
    env = dict(os.environ, BENCH_GC=mode, PYTHONPATH=".")
    out = subprocess.run(
        [sys.executable, "benchmarks/benchmark_end_to_end.py"],
        env=env, capture_output=True, text=True, check=True,
    ).stdout
    result = {}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, out)
        if match is None:
            raise RuntimeError(f"Could not parse {key} from output:\n{out}")
        result[key] = float(match.group(1))
    return result


def main():
    runs = {"on": [], "off": []}
    for i in range(ROUNDS):
        order = ("on", "off") if i % 2 == 0 else ("off", "on")
        for mode in order:
            r = run_once(mode)
            runs[mode].append(r)
            print(f"round {i + 1:2d} gc={mode:3s} thr={r['throughput']:9.0f} "
                  f"eng_med={r['engine_median_us']:6.2f} us "
                  f"eng_p99={r['engine_p99_us']:6.2f} us", flush=True)

    print("\nMedians over", ROUNDS, "rounds each (alternating order):")
    print(f"{'metric':18s} {'gc on':>12s} {'gc off':>12s}")
    for key in PATTERNS:
        on = statistics.median(x[key] for x in runs["on"])
        off = statistics.median(x[key] for x in runs["off"])
        print(f"{key:18s} {on:12.2f} {off:12.2f}")


if __name__ == "__main__":
    main()

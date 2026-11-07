"""Live curses dashboard: producer -> ring buffer -> consumer/engine -> screen.

Simulated data only. Latency shown is end-to-end (producer timestamp to after
add_order), which includes queueing delay in the ring buffer.
"""
import curses
import multiprocessing
import os
import subprocess
import sys
import tempfile
import time
from collections import deque
from queue import Empty, Full

from src.latency_io import write_latency_csv
from src.latency_stats import LatencyWindow
from src.live_snapshot import format_status_lines, make_snapshot
from src.matching_engine import MatchingEngine
from src.ring_buffer import RingBuffer
from src.trade_store import TradeStore

CAPACITY = 1024
REFRESH_S = 0.1


def dashboard_consumer(path, capacity, lock, order_count, snapshot_queue,
                       db_path=None, latency_csv=None):
    buffer = RingBuffer(path, capacity, lock=lock)
    engine = MatchingEngine()
    window = LatencyWindow(1000)
    store = TradeStore(db_path) if db_path else None
    samples = deque(maxlen=5000)
    last_csv = 0.0
    received = 0
    start = time.perf_counter()
    last_snap = start
    try:
        while received < order_count:
            order = buffer.get()
            if order is None:
                time.sleep(0)
                continue
            new_trades = engine.add_order(order)
            if store is not None:
                store.submit(new_trades)
            lat = time.perf_counter_ns() - order.timestamp_ns
            window.add(lat)
            if latency_csv:
                samples.append(lat)
            received += 1
            now = time.perf_counter()
            if now - last_snap >= REFRESH_S:
                last_snap = now
                if latency_csv and now - last_csv >= 1.0:
                    last_csv = now
                    write_latency_csv(latency_csv, samples)
                snap = make_snapshot(engine, window, received,
                                     received / (now - start),
                                     side_by_side=True)
                snap["done"] = False
                try:
                    snapshot_queue.put_nowait(snap)
                except Full:
                    pass
        end = time.perf_counter()
        if latency_csv:
            write_latency_csv(latency_csv, samples)
        final = make_snapshot(engine, window, received,
                              received / max(end - start, 1e-9),
                              side_by_side=True)
        final["done"] = True
        try:
            snapshot_queue.put(final, timeout=5)
        except Full:
            pass
    finally:
        buffer.close()
        if store is not None:
            store.close()


def screen_lines(snapshot):
    lines = format_status_lines(snapshot) + list(snapshot["lines"])
    if snapshot.get("done"):
        lines.append("")
        lines.append("FINISHED - all orders processed. Press q to quit.")
    return lines


def line_color(text):
    """Pick a color name for a screen line (pure function, testable)."""
    if text.startswith("CHRONOSMATCH") or text.startswith("FINISHED"):
        return "title"
    if text.startswith("BUY ORDERS"):
        return "buy"
    if text.startswith("SELL ORDERS"):
        return "sell"
    if text.startswith("RECENT TRADES"):
        return "title"
    if text.startswith("SPREAD"):
        return "stat"
    if text.startswith("BUY (") or text.startswith("ID "):
        return "title"
    if "*" in text:
        return "whale"
    if text.startswith("end-to-end latency") or text.startswith("orders received"):
        return "stat"
    return "plain"


def start_plot(csv_path):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return subprocess.Popen(
        [sys.executable, "-m", "src.latency_plot", csv_path], cwd=root,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_plot(proc):
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def toggle_plot(proc, start):
    """Stop the graph process if it is running, otherwise start a new one."""
    if proc is not None and proc.poll() is None:
        stop_plot(proc)
        return None
    return start()


def _init_colors():
    pairs = {}
    if curses.has_colors():
        curses.start_color()
        try:
            curses.use_default_colors()
        except curses.error:
            pass
        for index, (name, fg) in enumerate(
            [("title", curses.COLOR_CYAN), ("buy", curses.COLOR_GREEN),
             ("sell", curses.COLOR_RED), ("stat", curses.COLOR_YELLOW),
             ("whale", curses.COLOR_MAGENTA)],
            start=1,
        ):
            curses.init_pair(index, fg, -1)
            pairs[name] = curses.color_pair(index) | curses.A_BOLD
    return pairs


def _loop(stdscr, snapshot_queue, plot_csv=None):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    colors = _init_colors()
    latest = None
    plot = None
    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            stop_plot(plot)
            return
        if key in (ord("g"), ord("G")) and plot_csv:
            plot = toggle_plot(plot, lambda: start_plot(plot_csv))
        while True:
            try:
                latest = snapshot_queue.get_nowait()
            except Empty:
                break
        if latest is not None:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            lines = screen_lines(latest)
            footer = []
            if latest.get("done"):
                footer = lines[-1:]
                lines = lines[:-2]
            visible = lines[: max(height - 1 - len(footer), 0)]
            for row, text in enumerate(visible):
                attr = colors.get(line_color(text), 0)
                stdscr.addstr(row, 0, text[: width - 1], attr)
            for i, text in enumerate(footer):
                stdscr.addstr(height - len(footer) + i, 0, text[: width - 1],
                              colors.get("title", 0))
            stdscr.refresh()
        time.sleep(0.05)


def run_curses(snapshot_queue, plot_csv=None):
    curses.wrapper(_loop, snapshot_queue, plot_csv)


def main(order_count=300_000, db_path=None):
    from benchmarks.benchmark_end_to_end import producer_process

    context = multiprocessing.get_context("spawn")
    lock = context.Lock()
    snapshot_queue = context.Queue(maxsize=2)
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "live.bin")
        latency_csv = os.path.join(directory, "latency.csv")
        creator = RingBuffer(path, CAPACITY, create=True, lock=lock)
        consumer = context.Process(
            target=dashboard_consumer,
            args=(path, CAPACITY, lock, order_count, snapshot_queue, db_path,
                  latency_csv))
        producer = context.Process(
            target=producer_process,
            args=(path, CAPACITY, lock, order_count))
        try:
            consumer.start()
            producer.start()
            run_curses(snapshot_queue, latency_csv)
        finally:
            for process in (producer, consumer):
                if process.is_alive():
                    process.terminate()
                process.join()
            creator.close()
            snapshot_queue.close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300_000,
         sys.argv[2] if len(sys.argv) > 2 else None)

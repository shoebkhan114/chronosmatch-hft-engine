"""Live latency graph (matplotlib). Run: python -m src.latency_plot <latency.csv>

Started by the dashboard when you press g. matplotlib is imported only here.
"""
import sys

from src.latency_io import latency_stats_us, load_latencies


def main(csv_path):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    try:
        fig.canvas.manager.set_window_title("ChronosMatch - Latency Monitor")
    except Exception:
        pass
    fig.suptitle("ChronosMatch live end-to-end latency "
                 "(producer timestamp to after matching, includes queueing)")

    def update(_frame):
        values = load_latencies(csv_path)
        ax1.clear()
        ax2.clear()
        stats = latency_stats_us(values)
        if stats:
            ax1.plot(values, color="tab:blue", linewidth=0.8,
                     label="latency per order")
            ax1.axhline(stats["median"], color="tab:green", linestyle="--",
                        label=f"median {stats['median']:.0f} us")
            ax1.axhline(stats["p99"], color="tab:orange", linestyle="--",
                        label=f"p99 {stats['p99']:.0f} us")
            ax1.axhline(stats["max"], color="tab:red", linestyle=":",
                        label=f"max {stats['max']:.0f} us")
            ax1.set_yscale("log")
            ax1.legend(loc="upper left", fontsize=8)
            ax2.hist(values, bins=50, color="tab:purple", edgecolor="white",
                     label=f"{len(values)} samples")
            ax2.axvline(stats["median"], color="tab:green", linestyle="--",
                        label="median")
            ax2.axvline(stats["p99"], color="tab:orange", linestyle="--",
                        label="p99")
            ax2.legend(loc="upper right", fontsize=8)
        else:
            ax1.text(0.5, 0.5, "waiting for data...", ha="center",
                     transform=ax1.transAxes)
        ax1.set_title("Latency of the most recent orders (log scale)")
        ax1.set_xlabel("order (oldest to newest)")
        ax1.set_ylabel("latency (us)")
        ax1.grid(True, alpha=0.3)
        ax2.set_title("Latency distribution")
        ax2.set_xlabel("latency (us)")
        ax2.set_ylabel("number of orders")
        ax2.grid(True, alpha=0.3)
        fig.tight_layout(rect=[0, 0, 1, 0.95])

    animation = FuncAnimation(fig, update, interval=1000, cache_frame_data=False)
    update(0)
    plt.show()
    return animation


if __name__ == "__main__":
    main(sys.argv[1])

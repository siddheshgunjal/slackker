import os
import itertools
import matplotlib.pyplot as plt
from slackker.utils.logger import log


def generate_plot(model_name: str, export: str, logs: dict, metric: str) -> str | None:
    """Generate a training metric plot and save to disk. Returns the file path, or None on failure."""
    try:
        if not logs:
            log.error("Loss is missing from training history")
            return None

        first_key = next(iter(logs))
        epochs = range(len(logs[first_key]))

        color_cycle = ['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-', 'orange', 'darkviolet', 'fuchsia']
        colors_iter = iter(color_cycle)

        path = f"{model_name}_{metric}.{export}"

        plt.figure(figsize=(15, 8))
        for key, values in logs.items():
            if metric in key.lower():
                plt.plot(epochs, values, next(colors_iter), lw=2.5, label=f"{key}: {values[-1]:.4f}")
        plt.title(f"{model_name}_{metric}_Graph", fontsize=20)
        plt.xlabel("Epochs", fontsize=15)
        plt.ylabel(metric, fontsize=15)
        plt.legend(fontsize=12)
        plt.grid(True)
        plt.savefig(path)
        plt.close()

        return path
    except Exception as e:
        log.error(f"Plot generation failed: {e}")
        return None


def generate_and_get_plots(model_name: str, export: str, training_logs: dict, metrics: list[str] | None = None) -> list[str]:
    """Generate plots for specified metrics (default: loss + acc). Returns list of file paths."""
    if metrics is None:
        metrics = ["loss", "acc"]

    paths = []
    for metric in metrics:
        path = generate_plot(model_name, export, training_logs, metric)
        if path:
            paths.append(path)
    return paths

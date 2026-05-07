"""Tests for slackker.utils.plotting."""

import pytest
from unittest.mock import patch, MagicMock, call
from slackker.utils.plotting import generate_plot, generate_and_get_plots


# ── generate_plot ─────────────────────────────────────────────────────────────

class TestGeneratePlot:
    """Tests for generate_plot()."""

    def test_returns_path_for_matching_metric(self):
        logs = {"train_loss": [0.9, 0.7, 0.5], "val_loss": [0.85, 0.65, 0.45]}
        with patch("slackker.utils.plotting.plt") as mock_plt:
            result = generate_plot("MyModel", "png", logs, "loss")

        assert result == "MyModel_loss.png"
        mock_plt.figure.assert_called_once()
        mock_plt.savefig.assert_called_once_with("MyModel_loss.png")
        mock_plt.close.assert_called_once()

    def test_returns_path_for_acc_metric(self):
        logs = {"train_acc": [0.6, 0.75, 0.85], "val_acc": [0.55, 0.70, 0.80]}
        with patch("slackker.utils.plotting.plt") as mock_plt:
            result = generate_plot("Model", "svg", logs, "acc")

        assert result == "Model_acc.svg"
        mock_plt.savefig.assert_called_once_with("Model_acc.svg")

    def test_returns_none_for_empty_logs(self):
        result = generate_plot("Model", "png", {}, "loss")
        assert result is None

    def test_returns_none_on_exception(self):
        logs = {"train_loss": [0.5, 0.4]}
        with patch("slackker.utils.plotting.plt.figure", side_effect=RuntimeError("backend error")):
            result = generate_plot("Model", "png", logs, "loss")
        assert result is None

    def test_no_matching_metric_still_returns_path(self):
        """Logs exist but none contain the requested metric — empty plot is still saved."""
        logs = {"train_acc": [0.7, 0.8]}
        with patch("slackker.utils.plotting.plt") as mock_plt:
            result = generate_plot("Model", "png", logs, "loss")

        assert result == "Model_loss.png"
        mock_plt.savefig.assert_called_once_with("Model_loss.png")

    def test_plots_each_matching_key(self):
        """All log keys containing the metric name are plotted."""
        logs = {
            "train_loss": [0.9, 0.7],
            "val_loss": [0.85, 0.65],
            "other_metric": [1.0, 0.9],
        }
        plot_calls = []
        with patch("slackker.utils.plotting.plt") as mock_plt:
            mock_plt.plot = MagicMock(side_effect=lambda *a, **kw: plot_calls.append(a))
            generate_plot("M", "png", logs, "loss")

        # Only keys containing "loss" should be plotted
        assert len(plot_calls) == 2

    def test_returns_none_for_none_logs(self):
        result = generate_plot("Model", "png", None, "loss")
        assert result is None


# ── generate_and_get_plots ────────────────────────────────────────────────────

class TestGenerateAndGetPlots:
    """Tests for generate_and_get_plots()."""

    def test_default_metrics_generates_loss_and_acc(self):
        with patch("slackker.utils.plotting.generate_plot", return_value="/tmp/plot.png") as mock_gen:
            result = generate_and_get_plots("M", "png", {"train_loss": [0.5], "train_acc": [0.8]})

        assert len(result) == 2
        assert mock_gen.call_count == 2
        called_metrics = [c.args[3] for c in mock_gen.call_args_list]
        assert "loss" in called_metrics
        assert "acc" in called_metrics

    def test_custom_single_metric(self):
        with patch("slackker.utils.plotting.generate_plot", return_value="/tmp/p.png") as mock_gen:
            result = generate_and_get_plots("M", "png", {"train_loss": [0.5]}, metrics=["train_loss"])

        assert len(result) == 1
        mock_gen.assert_called_once_with("M", "png", {"train_loss": [0.5]}, "train_loss")

    def test_skips_none_returns_from_generate_plot(self):
        """Failed plots (None) are not included in the result."""
        with patch("slackker.utils.plotting.generate_plot", return_value=None):
            result = generate_and_get_plots("M", "png", {"loss": []})

        assert result == []

    def test_mixed_success_and_failure(self):
        side_effects = ["/tmp/loss.png", None]
        with patch("slackker.utils.plotting.generate_plot", side_effect=side_effects):
            result = generate_and_get_plots("M", "png", {"loss": [0.5], "acc": [0.8]})

        assert result == ["/tmp/loss.png"]

    def test_custom_multiple_metrics(self):
        with patch("slackker.utils.plotting.generate_plot", return_value="/tmp/p.png") as mock_gen:
            result = generate_and_get_plots(
                "M", "png", {"a": [1], "b": [2], "c": [3]},
                metrics=["a", "b", "c"],
            )

        assert len(result) == 3
        assert mock_gen.call_count == 3

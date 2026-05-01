"""Tests for slackker.callbacks.lightning module."""

import argparse
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from slackker.callbacks.lightning import SlackUpdate, TelegramUpdate


def _trainer_with_metrics(metrics):
    return SimpleNamespace(callback_metrics=metrics)


class TestSlackUpdateLightningInitialization:
    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.WebClient")
    def test_init_success(self, mock_web_client, mock_slack_connect, mock_check_internet):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        callback = SlackUpdate(
            token="xoxb-test",
            channel="C123",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
            export="png",
            SendPlot=True,
            verbose=2,
        )

        assert callback.ModelName == "Lightning NN Testing"
        assert callback.TrackLogs == ["train_loss", "train_acc", "val_loss", "val_acc"]
        assert callback.monitor == "val_loss"
        assert callback.export == "png"
        assert callback.SendPlot is True
        assert callback.verbose == 2
        assert callback.training_logs == {}
        assert callback.n_epochs == 0
        mock_web_client.assert_called_once_with(token="xoxb-test")

    @patch("slackker.callbacks.lightning.colors.prRed")
    def test_init_with_none_token(self, mock_pr_red):
        SlackUpdate(
            token=None,
            channel="C123",
            ModelName="Model",
            TrackLogs=["train_loss"],
            monitor="train_loss",
        )
        mock_pr_red.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.colors.prRed")
    @patch("slackker.callbacks.lightning.sys.exit")
    def test_init_requires_tracklogs(
        self,
        mock_exit,
        mock_pr_red,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            SlackUpdate(
                token="xoxb-test",
                channel="C123",
                ModelName="Model",
                TrackLogs=None,
                monitor="val_loss",
            )

        mock_pr_red.assert_called()
        mock_exit.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.WebClient")
    def test_init_export_none_raises(self, mock_web_client, mock_slack_connect, mock_check_internet):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        with pytest.raises(argparse.ArgumentTypeError):
            SlackUpdate(
                token="xoxb-test",
                channel="C123",
                ModelName="Model",
                TrackLogs=["train_loss"],
                monitor="train_loss",
                export=None,
            )

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.colors.prYellow")
    @patch("slackker.callbacks.lightning.WebClient")
    def test_init_monitor_none_warns(self, mock_web_client, mock_pr_yellow, mock_slack_connect, mock_check_internet):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        SlackUpdate(
            token="xoxb-test",
            channel="C123",
            ModelName="Model",
            TrackLogs=["train_loss", "val_loss"],
            monitor=None,
        )

        mock_pr_yellow.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.colors.prRed")
    @patch("slackker.callbacks.lightning.sys.exit")
    def test_init_tracklogs_must_be_list(
        self,
        mock_exit,
        mock_pr_red,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            SlackUpdate(
                token="xoxb-test",
                channel="C123",
                ModelName="Model",
                TrackLogs="train_loss",
                monitor="train_loss",
            )

        mock_pr_red.assert_called()
        mock_exit.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.colors.prRed")
    @patch("slackker.callbacks.lightning.sys.exit")
    def test_init_monitor_must_be_in_tracklogs(
        self,
        mock_exit,
        mock_pr_red,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            SlackUpdate(
                token="xoxb-test",
                channel="C123",
                ModelName="Model",
                TrackLogs=["train_loss", "val_loss"],
                monitor="val_acc",
            )

        mock_pr_red.assert_called()
        mock_exit.assert_called_once()


class TestSlackUpdateLightningCallbacks:
    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.WebClient")
    @patch("slackker.callbacks.lightning.functions.Slack.report_stats")
    def test_on_fit_start_posts_training_start(
        self,
        mock_report,
        mock_web_client,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        callback = SlackUpdate(
            token="xoxb-test",
            channel="C123",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
        )

        callback.on_fit_start(trainer=None, pl_module=None)

        mock_report.assert_called_once()
        assert "Lightning NN Testing" in mock_report.call_args.kwargs["text"]

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.WebClient")
    @patch("slackker.callbacks.lightning.checkker.check_internet_epoch_end")
    @patch("slackker.callbacks.lightning.functions.Slack.report_stats")
    def test_on_train_epoch_end_tracks_metrics_and_reports(
        self,
        mock_report,
        mock_epoch_internet,
        mock_web_client,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        mock_epoch_internet.return_value = True

        callback = SlackUpdate(
            token="xoxb-test",
            channel="C123",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
        )

        trainer = _trainer_with_metrics(
            {
                "train_loss": 0.90,
                "train_acc": 0.62,
                "val_loss": 0.84,
                "val_acc": 0.67,
            }
        )

        callback.on_train_epoch_end(trainer=trainer, pl_module=None)

        assert callback.n_epochs == 1
        assert callback.training_logs["train_loss"] == [0.90]
        assert callback.training_logs["train_acc"] == [0.62]
        assert callback.training_logs["val_loss"] == [0.84]
        assert callback.training_logs["val_acc"] == [0.67]
        mock_report.assert_called_once()
        assert "Epoch: 0" in mock_report.call_args.kwargs["text"]

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.WebClient")
    @patch("slackker.callbacks.lightning.checkker.check_internet_epoch_end")
    @patch("slackker.callbacks.lightning.functions.Slack.report_stats")
    def test_on_train_epoch_end_skips_report_without_internet(
        self,
        mock_report,
        mock_epoch_internet,
        mock_web_client,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        mock_epoch_internet.return_value = False

        callback = SlackUpdate(
            token="xoxb-test",
            channel="C123",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
        )

        trainer = _trainer_with_metrics(
            {
                "train_loss": 0.90,
                "train_acc": 0.62,
                "val_loss": 0.84,
                "val_acc": 0.67,
            }
        )

        callback.on_train_epoch_end(trainer=trainer, pl_module=None)

        assert callback.n_epochs == 1
        assert callback.training_logs["val_loss"] == [0.84]
        mock_report.assert_not_called()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.WebClient")
    @patch("slackker.callbacks.lightning.functions.Slack.report_stats")
    @patch("slackker.callbacks.lightning.functions.Slack.lightning_plot_history")
    def test_on_fit_end_reports_best_epoch_with_loss_monitor(
        self,
        mock_plot_history,
        mock_report,
        mock_web_client,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        callback = SlackUpdate(
            token="xoxb-test",
            channel="C123",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
            SendPlot=True,
        )
        callback.training_logs = {
            "train_loss": [0.9, 0.7, 0.5],
            "train_acc": [0.6, 0.7, 0.8],
            "val_loss": [0.8, 0.4, 0.6],
            "val_acc": [0.65, 0.75, 0.72],
        }
        callback.n_epochs = 3

        callback.on_fit_end(trainer=None, pl_module=None)

        mock_report.assert_called_once()
        assert "Best epoch was, Epoch 1" in mock_report.call_args.kwargs["text"]
        mock_plot_history.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.WebClient")
    @patch("slackker.callbacks.lightning.functions.Slack.report_stats")
    @patch("slackker.callbacks.lightning.functions.Slack.lightning_plot_history")
    def test_on_fit_end_without_monitor_uses_fallback_message(
        self,
        mock_plot_history,
        mock_report,
        mock_web_client,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        callback = SlackUpdate(
            token="xoxb-test",
            channel="C123",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor=None,
        )
        callback.training_logs = {
            "train_loss": [0.9],
            "train_acc": [0.6],
            "val_loss": [0.8],
            "val_acc": [0.65],
        }
        callback.n_epochs = 1

        callback.on_fit_end(trainer=None, pl_module=None)

        mock_report.assert_called_once()
        assert "monitor' was not provided" in mock_report.call_args.kwargs["text"]
        mock_plot_history.assert_called_once()
        assert mock_plot_history.call_args.kwargs["training_logs"] == callback.training_logs

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.slack_connect")
    @patch("slackker.callbacks.lightning.WebClient")
    @patch("slackker.callbacks.lightning.functions.Slack.report_stats")
    @patch("slackker.callbacks.lightning.functions.Slack.lightning_plot_history")
    def test_on_fit_end_reports_best_epoch_with_acc_monitor(
        self,
        mock_plot_history,
        mock_report,
        mock_web_client,
        mock_slack_connect,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        callback = SlackUpdate(
            token="xoxb-test",
            channel="C123",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_acc",
        )
        callback.training_logs = {
            "val_acc": [0.50, 0.72, 0.69],
            "val_loss": [0.7, 0.5, 0.6],
        }
        callback.n_epochs = 3

        callback.on_fit_end(trainer=None, pl_module=None)

        mock_report.assert_called_once()
        assert "Best epoch was, Epoch 1" in mock_report.call_args.kwargs["text"]
        mock_plot_history.assert_called_once()


class TestTelegramUpdateLightningInitialization:
    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    def test_init_success(self, mock_get_chat_id, mock_check_internet):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        callback = TelegramUpdate(
            token="telegram-token",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
            export="png",
            SendPlot=True,
            verbose=2,
        )

        assert callback.token == "telegram-token"
        assert callback.channel == "987654321"
        assert callback.TrackLogs == ["train_loss", "train_acc", "val_loss", "val_acc"]
        assert callback.monitor == "val_loss"
        assert callback.training_logs == {}
        assert callback.n_epochs == 0

    @patch("slackker.callbacks.lightning.colors.prRed")
    def test_init_with_none_token(self, mock_pr_red):
        TelegramUpdate(
            token=None,
            ModelName="Model",
            TrackLogs=["train_loss"],
            monitor="train_loss",
        )
        mock_pr_red.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.sys.exit")
    @patch("slackker.callbacks.lightning.colors.prRed")
    def test_init_requires_tracklogs(
        self,
        mock_pr_red,
        mock_exit,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            TelegramUpdate(
                token="telegram-token",
                ModelName="Model",
                TrackLogs=None,
                monitor="val_loss",
            )

        mock_pr_red.assert_called()
        mock_exit.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.sys.exit")
    @patch("slackker.callbacks.lightning.colors.prRed")
    def test_init_tracklogs_must_be_list(
        self,
        mock_pr_red,
        mock_exit,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            TelegramUpdate(
                token="telegram-token",
                ModelName="Model",
                TrackLogs="train_loss",
                monitor="train_loss",
            )

        mock_pr_red.assert_called()
        mock_exit.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.colors.prRed")
    @patch("slackker.callbacks.lightning.sys.exit")
    def test_init_monitor_must_be_in_tracklogs(
        self,
        mock_exit,
        mock_pr_red,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            TelegramUpdate(
                token="telegram-token",
                ModelName="Model",
                TrackLogs=["train_loss", "val_loss"],
                monitor="val_acc",
            )

        mock_pr_red.assert_called()
        mock_exit.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.colors.prYellow")
    def test_init_monitor_none_warns(self, mock_pr_yellow, mock_get_chat_id, mock_check_internet):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        TelegramUpdate(
            token="telegram-token",
            ModelName="Model",
            TrackLogs=["train_loss", "val_loss"],
            monitor=None,
        )

        mock_pr_yellow.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    def test_init_export_none_raises(self, mock_get_chat_id, mock_check_internet):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        with pytest.raises(argparse.ArgumentTypeError):
            TelegramUpdate(
                token="telegram-token",
                ModelName="Model",
                TrackLogs=["train_loss"],
                monitor="train_loss",
                export=None,
            )


class TestTelegramUpdateLightningCallbacks:
    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.functions.Telegram.report_stats")
    def test_on_fit_start_posts_training_start(
        self,
        mock_report,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        callback = TelegramUpdate(
            token="telegram-token",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
        )

        callback.on_fit_start(trainer=None, pl_module=None)

        mock_report.assert_called_once()
        assert "Lightning NN Testing" in mock_report.call_args.kwargs["text"]

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.checkker.check_internet_epoch_end")
    @patch("slackker.callbacks.lightning.functions.Telegram.report_stats")
    def test_on_train_epoch_end_tracks_metrics_and_reports(
        self,
        mock_report,
        mock_epoch_internet,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"
        mock_epoch_internet.return_value = True

        callback = TelegramUpdate(
            token="telegram-token",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
        )

        trainer = _trainer_with_metrics(
            {
                "train_loss": 0.90,
                "train_acc": 0.62,
                "val_loss": 0.84,
                "val_acc": 0.67,
            }
        )

        callback.on_train_epoch_end(trainer=trainer, pl_module=None)

        assert callback.n_epochs == 1
        assert callback.training_logs["val_loss"] == [0.84]
        mock_report.assert_called_once()
        assert "Epoch: 0" in mock_report.call_args.kwargs["text"]

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.checkker.check_internet_epoch_end")
    @patch("slackker.callbacks.lightning.functions.Telegram.report_stats")
    def test_on_train_epoch_end_no_internet_skips_report(
        self,
        mock_report,
        mock_epoch_internet,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"
        mock_epoch_internet.return_value = False

        callback = TelegramUpdate(
            token="telegram-token",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
        )

        trainer = _trainer_with_metrics(
            {
                "train_loss": 0.90,
                "train_acc": 0.62,
                "val_loss": 0.84,
                "val_acc": 0.67,
            }
        )

        callback.on_train_epoch_end(trainer=trainer, pl_module=None)

        assert callback.n_epochs == 1
        assert callback.training_logs["val_loss"] == [0.84]
        mock_report.assert_not_called()
        mock_epoch_internet.assert_called_once_with(url="www.slack.com")

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.functions.Telegram.report_stats")
    @patch("slackker.callbacks.lightning.functions.Telegram.lightning_plot_history")
    def test_on_fit_end_reports_best_epoch_with_loss_monitor(
        self,
        mock_plot_history,
        mock_report,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        callback = TelegramUpdate(
            token="telegram-token",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
            SendPlot=True,
        )
        callback.training_logs = {
            "train_loss": [0.9, 0.7, 0.5],
            "train_acc": [0.6, 0.7, 0.8],
            "val_loss": [0.8, 0.4, 0.6],
            "val_acc": [0.65, 0.75, 0.72],
        }
        callback.n_epochs = 3

        callback.on_fit_end(trainer=None, pl_module=None)

        mock_report.assert_called_once()
        assert "Best epoch was, Epoch 1" in mock_report.call_args.kwargs["text"]
        mock_plot_history.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.functions.Telegram.report_stats")
    @patch("slackker.callbacks.lightning.functions.Telegram.lightning_plot_history")
    def test_on_fit_end_reports_best_epoch_with_acc_monitor(
        self,
        mock_plot_history,
        mock_report,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        callback = TelegramUpdate(
            token="telegram-token",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_acc",
        )
        callback.training_logs = {
            "val_acc": [0.50, 0.72, 0.69],
            "val_loss": [0.7, 0.5, 0.6],
        }
        callback.n_epochs = 3

        callback.on_fit_end(trainer=None, pl_module=None)

        mock_report.assert_called_once()
        assert "Best epoch was, Epoch 1" in mock_report.call_args.kwargs["text"]
        mock_plot_history.assert_called_once()

    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.functions.Telegram.report_stats")
    @patch("slackker.callbacks.lightning.functions.Telegram.lightning_plot_history")
    def test_on_fit_end_without_monitor_uses_fallback_message(
        self,
        mock_plot_history,
        mock_report,
        mock_get_chat_id,
        mock_check_internet,
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"

        callback = TelegramUpdate(
            token="telegram-token",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor=None,
        )
        callback.training_logs = {
            "train_loss": [0.9],
            "train_acc": [0.6],
            "val_loss": [0.8],
            "val_acc": [0.65],
        }
        callback.n_epochs = 1

        callback.on_fit_end(trainer=None, pl_module=None)

        mock_report.assert_called_once()
        assert "monitor' was not provided" in mock_report.call_args.kwargs["text"]
        mock_plot_history.assert_called_once()


class TestLightningWorkflowIntegration:
    @patch("slackker.callbacks.lightning.checkker.check_internet")
    @patch("slackker.callbacks.lightning.checkker.get_telegram_chat_id")
    @patch("slackker.callbacks.lightning.checkker.check_internet_epoch_end")
    @patch("slackker.callbacks.lightning.functions.Telegram.report_stats")
    @patch("slackker.callbacks.lightning.functions.Telegram.lightning_plot_history")
    def test_telegram_reference_workflow_from_sample(
        self,
        mock_plot_history,
        mock_report,
        mock_epoch_internet,
        mock_get_chat_id,
        mock_check_internet,
    ):
        """Simulates the sample Trainer workflow in the user example."""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "987654321"
        mock_epoch_internet.return_value = True

        callback = TelegramUpdate(
            token="6703340847:AAECWu8qLPTIRMDGjXjzwT5UbK_9P13WdK8",
            ModelName="Lightning NN Testing",
            TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
            monitor="val_loss",
            export="png",
            SendPlot=True,
            verbose=2,
        )

        callback.on_fit_start(trainer=None, pl_module=None)

        for epoch in range(6):
            trainer = _trainer_with_metrics(
                {
                    "train_loss": 0.90 - (0.05 * epoch),
                    "train_acc": 0.60 + (0.04 * epoch),
                    "val_loss": 0.85 - (0.04 * epoch),
                    "val_acc": 0.62 + (0.03 * epoch),
                }
            )
            callback.on_train_epoch_end(trainer=trainer, pl_module=None)

        callback.on_fit_end(trainer=None, pl_module=None)

        assert callback.n_epochs == 6
        assert len(callback.training_logs["train_loss"]) == 6
        assert len(callback.training_logs["val_loss"]) == 6
        assert mock_report.call_count == 8
        mock_plot_history.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

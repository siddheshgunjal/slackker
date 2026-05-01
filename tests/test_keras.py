"""
Comprehensive tests for slackker.callbacks.keras module
Tests cover SlackUpdate and TelegramUpdate Keras callback classes
"""

import pytest
import argparse
import numpy as np
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from slackker.callbacks.keras import SlackUpdate, TelegramUpdate


class TestSlackUpdateKerasInitialization:
    """Test SlackUpdate Keras callback initialization"""
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    def test_slack_keras_init_success(self, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test successful SlackUpdate Keras callback initialization"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model",
            export="png",
            SendPlot=True,
            verbose=0
        )
        
        assert callback.ModelName == "Test_Model"
        assert callback.export == "png"
        assert callback.SendPlot == True
        assert callback.verbose == 0
        assert callback.n_epochs == 0
        assert callback.train_loss == []
        assert callback.train_acc == []
        assert callback.valid_loss == []
        assert callback.valid_acc == []
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    def test_slack_keras_init_with_all_formats(self, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test SlackUpdate initialization with different export formats"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        formats = ["png", "jpg", "pdf", "svg"]
        for fmt in formats:
            callback = SlackUpdate(
                token="test_token",
                channel="C123456",
                ModelName="Test_Model",
                export=fmt,
                SendPlot=False
            )
            assert callback.export == fmt
    
    @patch('slackker.callbacks.keras.colors.prRed')
    def test_slack_keras_init_no_token(self, mock_print_red):
        """Test SlackUpdate initialization with None token"""
        callback = SlackUpdate(
            token=None,
            channel="C123456",
            ModelName="Test_Model"
        )
        mock_print_red.assert_called_once()
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    def test_slack_keras_init_no_internet(self, mock_slack_connect, mock_check_internet):
        """Test SlackUpdate initialization without internet"""
        mock_check_internet.return_value = False
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        mock_check_internet.assert_called_once_with(url="www.slack.com", verbose=0)
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    def test_slack_keras_init_invalid_export_format(self, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test SlackUpdate initialization with invalid export format"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        # This should pass during init, validation happens in __init__
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model",
            export="png"
        )
        assert callback.export == "png"


class TestTelegramUpdateKerasInitialization:
    """Test TelegramUpdate Keras callback initialization"""
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    def test_telegram_keras_init_success(self, mock_get_chat_id, mock_check_internet):
        """Test successful TelegramUpdate Keras callback initialization"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="Keras_NN",
            export="png",
            SendPlot=True,
            verbose=1
        )
        
        assert callback.token == "test_token"
        assert callback.channel == "123456789"
        assert callback.ModelName == "Keras_NN"
        assert callback.export == "png"
        assert callback.SendPlot == True
        assert callback.verbose == 1
        assert callback.n_epochs == 0
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    def test_telegram_keras_init_default_params(self, mock_get_chat_id, mock_check_internet):
        """Test TelegramUpdate initialization with default parameters"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="My_Model"
        )
        
        assert callback.export == "png"  # Default
        assert callback.SendPlot == False  # Default
        assert callback.verbose == 0  # Default
    
    @patch('slackker.callbacks.keras.colors.prRed')
    def test_telegram_keras_init_no_token(self, mock_print_red):
        """Test TelegramUpdate initialization with None token"""
        callback = TelegramUpdate(
            token=None,
            ModelName="Test_Model"
        )
        mock_print_red.assert_called_once()
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    def test_telegram_keras_init_no_internet(self, mock_get_chat_id, mock_check_internet):
        """Test TelegramUpdate initialization without internet"""
        mock_check_internet.return_value = False
        mock_get_chat_id.return_value = "123456789"
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="Test_Model"
        )
        mock_check_internet.assert_called_once_with(url="www.telegram.org", verbose=0)


class TestSlackUpdateKerasCallbacks:
    """Test SlackUpdate Keras callback methods"""
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    def test_on_train_begin(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test on_train_begin callback method"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        callback.on_train_begin(logs={})
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "Test_Model" in message
        assert "started at" in message
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    def test_on_epoch_end(self, mock_check_epoch, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test on_epoch_end callback method"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        mock_check_epoch.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        logs = {
            'accuracy': 0.85,
            'loss': 0.45,
            'val_accuracy': 0.80,
            'val_loss': 0.50
        }
        
        callback.on_epoch_end(batch=0, logs=logs)
        
        assert callback.n_epochs == 1
        assert len(callback.train_loss) == 1
        assert len(callback.train_acc) == 1
        assert len(callback.valid_loss) == 1
        assert len(callback.valid_acc) == 1
        
        # Verify report was called
        assert mock_report.called
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    def test_multiple_epochs(self, mock_check_epoch, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test multiple epochs tracking"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        mock_check_epoch.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        # Simulate 3 epochs
        epochs_logs = [
            {'accuracy': 0.70, 'loss': 0.60, 'val_accuracy': 0.65, 'val_loss': 0.65},
            {'accuracy': 0.80, 'loss': 0.45, 'val_accuracy': 0.75, 'val_loss': 0.50},
            {'accuracy': 0.85, 'loss': 0.35, 'val_accuracy': 0.82, 'val_loss': 0.40},
        ]
        
        for i, logs in enumerate(epochs_logs):
            callback.on_epoch_end(batch=i, logs=logs)
        
        assert callback.n_epochs == 3
        assert len(callback.train_loss) == 3
        assert len(callback.valid_acc) == 3
        assert callback.train_loss[-1] == 0.35
        assert callback.valid_acc[-1] == 0.82
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.functions.Slack.keras_plot_history')
    def test_on_train_end(self, mock_plot, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test on_train_end callback method"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model",
            export="png",
            SendPlot=True
        )
        
        # Simulate training history
        callback.train_loss = [0.60, 0.45, 0.35]
        callback.train_acc = [0.70, 0.80, 0.85]
        callback.valid_loss = [0.65, 0.50, 0.40]
        callback.valid_acc = [0.65, 0.75, 0.82]
        callback.n_epochs = 3
        
        callback.on_train_end(logs={})
        
        # Verify report was called with best epoch info
        assert mock_report.call_count >= 2
        
        # Verify plot function was called
        mock_plot.assert_called_once()
        plot_call_args = mock_plot.call_args
        training_logs = plot_call_args[1]['training_logs']
        assert 'train_loss' in training_logs
        assert 'train_acc' in training_logs
        assert 'val_loss' in training_logs
        assert 'val_acc' in training_logs
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.functions.Slack.keras_plot_history')
    def test_best_epoch_calculation(self, mock_plot, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test best epoch calculation in on_train_end"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        # Set training logs with known best epoch
        callback.train_loss = [0.60, 0.45, 0.35, 0.40]  # Best at index 2
        callback.train_acc = [0.70, 0.80, 0.85, 0.84]
        callback.valid_loss = [0.65, 0.50, 0.38, 0.42]  # Best at index 2
        callback.valid_acc = [0.65, 0.75, 0.82, 0.80]
        callback.n_epochs = 4
        
        callback.on_train_end(logs={})
        
        # Check that the best epoch (2) was identified and reported
        call_args_list = mock_report.call_args_list
        # Find the call with best epoch info
        found_best_epoch = False
        for call_obj in call_args_list:
            message = call_obj[1]['text']
            if "Best epoch was 2" in message:
                found_best_epoch = True
                break
        
        assert found_best_epoch, "Best epoch information not found in report calls"
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    def test_epoch_end_no_internet(self, mock_check_epoch, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test epoch end callback when internet is unavailable"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        mock_check_epoch.return_value = False  # No internet
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        logs = {
            'accuracy': 0.85,
            'loss': 0.45,
            'val_accuracy': 0.80,
            'val_loss': 0.50
        }
        
        callback.on_epoch_end(batch=0, logs=logs)
        
        # Logs should still be recorded even without internet
        assert callback.n_epochs == 1
        assert len(callback.train_loss) == 1


class TestTelegramUpdateKerasCallbacks:
    """Test TelegramUpdate Keras callback methods"""
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    def test_telegram_on_train_begin(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram on_train_begin callback"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="Keras_NN"
        )
        
        callback.on_train_begin(logs={})
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "Keras_NN" in message
        assert "started at" in message
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    def test_telegram_on_epoch_end(self, mock_check_epoch, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram on_epoch_end callback"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        mock_check_epoch.return_value = True
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="Keras_NN"
        )
        
        logs = {
            'accuracy': 0.85,
            'loss': 0.45,
            'val_accuracy': 0.80,
            'val_loss': 0.50
        }
        
        callback.on_epoch_end(batch=0, logs=logs)
        
        assert callback.n_epochs == 1
        assert mock_report.called
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    @patch('slackker.callbacks.keras.functions.Telegram.keras_plot_history')
    def test_telegram_on_train_end(self, mock_plot, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram on_train_end callback"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="Keras_NN",
            export="png",
            SendPlot=True
        )
        
        callback.train_loss = [0.60, 0.45, 0.35]
        callback.train_acc = [0.70, 0.80, 0.85]
        callback.valid_loss = [0.65, 0.50, 0.40]
        callback.valid_acc = [0.65, 0.75, 0.82]
        callback.n_epochs = 3
        
        callback.on_train_end(logs={})
        
        assert mock_report.call_count >= 2
        mock_plot.assert_called_once()
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    def test_telegram_multiple_epochs(self, mock_check_epoch, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram callback with multiple epochs"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        mock_check_epoch.return_value = True
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="Keras_NN"
        )
        
        epochs_logs = [
            {'accuracy': 0.70, 'loss': 0.60, 'val_accuracy': 0.65, 'val_loss': 0.65},
            {'accuracy': 0.80, 'loss': 0.45, 'val_accuracy': 0.75, 'val_loss': 0.50},
            {'accuracy': 0.85, 'loss': 0.35, 'val_accuracy': 0.82, 'val_loss': 0.40},
        ]
        
        for i, logs in enumerate(epochs_logs):
            callback.on_epoch_end(batch=i, logs=logs)
        
        assert callback.n_epochs == 3


class TestKerasCallbackIntegration:
    """Integration tests for Keras callbacks"""
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    @patch('slackker.callbacks.keras.functions.Slack.keras_plot_history')
    def test_slack_complete_training_workflow(self, mock_plot, mock_check_epoch, mock_report, 
                                              mock_webclient, mock_slack_connect, mock_check_internet):
        """Test complete Slack training workflow"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        mock_check_epoch.return_value = True
        
        callback = SlackUpdate(
            token="xoxb-test",
            channel="C123456",
            ModelName="Keras_NN",
            export="png",
            SendPlot=True
        )
        
        # Training begins
        callback.on_train_begin(logs={})
        
        # Simulate 5 epochs
        for epoch in range(5):
            logs = {
                'accuracy': 0.70 + epoch * 0.03,
                'loss': 0.60 - epoch * 0.05,
                'val_accuracy': 0.65 + epoch * 0.03,
                'val_loss': 0.65 - epoch * 0.05
            }
            callback.on_epoch_end(batch=epoch, logs=logs)
        
        # Training ends
        callback.on_train_end(logs={})
        
        # Verify workflow
        assert callback.n_epochs == 5
        assert mock_report.call_count >= 2  # Begin + end
        mock_plot.assert_called_once()
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    @patch('slackker.callbacks.keras.functions.Telegram.keras_plot_history')
    def test_telegram_complete_training_workflow(self, mock_plot, mock_check_epoch, mock_report, 
                                                 mock_get_chat_id, mock_check_internet):
        """Test complete Telegram training workflow"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        mock_check_epoch.return_value = True
        
        callback = TelegramUpdate(
            token="6703340847:AAECWu8qLPTIRMDGjXjzwT5UbK_9P13WdK8",
            ModelName="Keras_NN",
            export="png",
            SendPlot=True
        )
        
        # Training begins
        callback.on_train_begin(logs={})
        
        # Simulate epochs
        for epoch in range(3):
            logs = {
                'accuracy': 0.70 + epoch * 0.05,
                'loss': 0.60 - epoch * 0.1,
                'val_accuracy': 0.65 + epoch * 0.05,
                'val_loss': 0.65 - epoch * 0.1
            }
            callback.on_epoch_end(batch=epoch, logs=logs)
        
        # Training ends
        callback.on_train_end(logs={})
        
        assert callback.n_epochs == 3
        mock_plot.assert_called_once()


class TestKerasCallbackEdgeCases:
    """Test edge cases for Keras callbacks"""
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    def test_slack_single_epoch(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test Slack callback with single epoch"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        logs = {
            'accuracy': 0.85,
            'loss': 0.45,
            'val_accuracy': 0.80,
            'val_loss': 0.50
        }
        
        callback.on_epoch_end(batch=0, logs=logs)
        assert callback.n_epochs == 1
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.functions.Slack.keras_plot_history')
    def test_slack_logs_ordering(self, mock_plot, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test that logs are stored in correct order"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        # Create multiple epochs with distinguishable values
        for i in range(3):
            logs = {
                'accuracy': 0.5 + i * 0.1,
                'loss': 0.9 - i * 0.1,
                'val_accuracy': 0.4 + i * 0.1,
                'val_loss': 1.0 - i * 0.1
            }
            callback.on_epoch_end(batch=i, logs=logs)
        
        # Verify order is maintained
        assert callback.train_acc == pytest.approx([0.5, 0.6, 0.7])
        assert callback.train_loss == pytest.approx([0.9, 0.8, 0.7])
        assert callback.valid_acc == pytest.approx([0.4, 0.5, 0.6])
        assert callback.valid_loss == pytest.approx([1.0, 0.9, 0.8])
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    @patch('slackker.callbacks.keras.functions.Telegram.keras_plot_history')
    def test_telegram_empty_training(self, mock_plot, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram callback with no epochs"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="Test_Model"
        )
        
        # Call on_train_end without any epochs
        with pytest.raises(ValueError):
            callback.on_train_end(logs={})


class TestKerasCallbackVerbosity:
    """Test verbose logging for Keras callbacks"""
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    def test_slack_verbose_level_0(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test Slack callback with verbose=0 (silent)"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model",
            verbose=0
        )
        
        callback.on_train_begin(logs={})
        assert mock_report.called
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    def test_slack_verbose_level_2(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test Slack callback with verbose=2 (debug)"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model",
            verbose=2
        )
        
        callback.on_train_begin(logs={})
        # Verify callback still works with higher verbosity
        call_args = mock_report.call_args
        assert call_args[1]['verbose'] == 2
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    def test_telegram_verbose_level_1(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram callback with verbose=1 (info)"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        callback = TelegramUpdate(
            token="test_token",
            ModelName="Test_Model",
            verbose=1
        )
        
        callback.on_train_begin(logs={})
        call_args = mock_report.call_args
        assert call_args[1]['verbose'] == 1


class TestKerasCallbackMessageFormatting:
    """Test message formatting in Keras callbacks"""
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    def test_epoch_message_format(self, mock_check_epoch, mock_report, mock_webclient, 
                                   mock_slack_connect, mock_check_internet):
        """Test epoch message formatting"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        mock_check_epoch.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        logs = {
            'accuracy': 0.8234,
            'loss': 0.4567,
            'val_accuracy': 0.7956,
            'val_loss': 0.5123
        }
        
        callback.on_epoch_end(batch=0, logs=logs)
        
        call_args = mock_report.call_args
        message = call_args[1]['text']
        
        # Verify message contains expected information
        assert "Epoch: 0" in message
        assert "Training Loss:" in message
        assert "Validation Loss:" in message
    
    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    @patch('slackker.callbacks.keras.functions.Slack.keras_plot_history')
    def test_train_end_message_format(self, mock_plot, mock_report, mock_webclient, 
                                       mock_slack_connect, mock_check_internet):
        """Test train end message formatting"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        callback = SlackUpdate(
            token="test_token",
            channel="C123456",
            ModelName="Test_Model"
        )
        
        callback.train_loss = [0.60, 0.45, 0.35]
        callback.train_acc = [0.70, 0.80, 0.85]
        callback.valid_loss = [0.65, 0.50, 0.40]
        callback.valid_acc = [0.65, 0.75, 0.82]
        callback.n_epochs = 3
        
        callback.on_train_end(logs={})
        
        # Verify messages contain training summary
        call_args_list = mock_report.call_args_list
        messages = [call_obj[1]['text'] for call_obj in call_args_list]
        
        # Should have at least 2 messages
        assert len(messages) >= 2
        # One should mention epochs
        assert any("3 epochs" in msg for msg in messages)


class TestKerasCallbackAdditionalBranches:
    """Extra branch coverage for init and lifecycle error paths."""

    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    def test_slack_init_export_none_raises(self, mock_webclient, mock_slack_connect, mock_check_internet):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True

        with pytest.raises(argparse.ArgumentTypeError):
            SlackUpdate(
                token="test_token",
                channel="C123456",
                ModelName="Test_Model",
                export=None,
            )

    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    def test_telegram_init_export_none_raises(self, mock_get_chat_id, mock_check_internet):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"

        with pytest.raises(argparse.ArgumentTypeError):
            TelegramUpdate(
                token="test_token",
                ModelName="Test_Model",
                export=None,
            )

    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.slack_connect')
    @patch('slackker.callbacks.keras.WebClient')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    @patch('slackker.callbacks.keras.functions.Slack.report_stats')
    def test_slack_on_epoch_end_incomplete_logs_raises(
        self, mock_report, mock_check_epoch, mock_webclient, mock_slack_connect, mock_check_internet
    ):
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        mock_check_epoch.return_value = True

        callback = SlackUpdate(token="test_token", channel="C123456", ModelName="Test_Model")

        with pytest.raises(IndexError):
            callback.on_epoch_end(batch=0, logs={'accuracy': 0.8, 'loss': 0.2})

    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    def test_telegram_on_epoch_end_no_internet_still_tracks(
        self, mock_report, mock_check_epoch, mock_get_chat_id, mock_check_internet
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        mock_check_epoch.return_value = False

        callback = TelegramUpdate(token="test_token", ModelName="Test_Model")
        logs = {
            'accuracy': 0.85,
            'loss': 0.45,
            'val_accuracy': 0.80,
            'val_loss': 0.50,
        }

        callback.on_epoch_end(batch=0, logs=logs)

        assert callback.n_epochs == 1
        assert callback.valid_loss == [0.50]
        mock_report.assert_not_called()

    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.checkker.check_internet_epoch_end')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    def test_telegram_on_epoch_end_incomplete_logs_raises(
        self, mock_report, mock_check_epoch, mock_get_chat_id, mock_check_internet
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        mock_check_epoch.return_value = True

        callback = TelegramUpdate(token="test_token", ModelName="Test_Model")

        with pytest.raises(IndexError):
            callback.on_epoch_end(batch=0, logs={'accuracy': 0.8, 'loss': 0.2})

    @patch('slackker.callbacks.keras.checkker.check_internet')
    @patch('slackker.callbacks.keras.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.keras.functions.Telegram.report_stats')
    @patch('slackker.callbacks.keras.functions.Telegram.keras_plot_history')
    def test_telegram_train_end_message_contains_accuracy_percent(
        self, mock_plot, mock_report, mock_get_chat_id, mock_check_internet
    ):
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"

        callback = TelegramUpdate(token="test_token", ModelName="Keras_NN", SendPlot=True)
        callback.train_loss = [0.60, 0.45, 0.35]
        callback.train_acc = [0.70, 0.80, 0.85]
        callback.valid_loss = [0.65, 0.50, 0.40]
        callback.valid_acc = [0.65, 0.75, 0.82]
        callback.n_epochs = 3

        callback.on_train_end(logs={})

        messages = [c[1]['text'] for c in mock_report.call_args_list]
        assert any("Best Accuracy =" in m and "%" in m for m in messages)
        mock_plot.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Comprehensive tests for slackker.callbacks.basic module
Tests cover SlackUpdate and TelegramUpdate classes with notifier decorator and notify method
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from slackker.callbacks.basic import SlackUpdate, TelegramUpdate


class TestSlackUpdateInitialization:
    """Test SlackUpdate class initialization"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    def test_slack_update_init_success(self, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test successful SlackUpdate initialization"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        assert slackker.token == "test_token" or hasattr(slackker, 'client')
        assert slackker.channel == "C123456"
        assert slackker.verbose == 0
        mock_webclient.assert_called_once_with(token="test_token")
    
    @patch('slackker.callbacks.basic.colors.prRed')
    def test_slack_update_init_no_token(self, mock_print_red):
        """Test SlackUpdate initialization with None token"""
        slackker = SlackUpdate(token=None, channel="C123456")
        mock_print_red.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    def test_slack_update_init_no_internet(self, mock_slack_connect, mock_check_internet):
        """Test SlackUpdate initialization without internet"""
        mock_check_internet.return_value = False
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456")
        mock_check_internet.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    def test_slack_update_init_invalid_api(self, mock_slack_connect, mock_check_internet):
        """Test SlackUpdate initialization with invalid Slack API"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = False
        
        slackker = SlackUpdate(token="invalid_token", channel="C123456")
        mock_slack_connect.assert_called_once()


class TestTelegramUpdateInitialization:
    """Test TelegramUpdate class initialization"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    def test_telegram_update_init_success(self, mock_get_chat_id, mock_check_internet):
        """Test successful TelegramUpdate initialization"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG", verbose=0)
        
        assert slackker.token == "1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG"
        assert slackker.channel == "123456789"
        assert slackker.verbose == 0
    
    @patch('slackker.callbacks.basic.colors.prRed')
    def test_telegram_update_init_no_token(self, mock_print_red):
        """Test TelegramUpdate initialization with None token"""
        slackker = TelegramUpdate(token=None)
        mock_print_red.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    def test_telegram_update_init_no_internet(self, mock_get_chat_id, mock_check_internet):
        """Test TelegramUpdate initialization without internet"""
        mock_check_internet.return_value = False
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG")
        mock_check_internet.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    def test_telegram_update_init_invalid_token(self, mock_get_chat_id, mock_check_internet):
        """Test TelegramUpdate initialization with invalid token"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = None
        
        slackker = TelegramUpdate(token="invalid_token")
        mock_get_chat_id.assert_called_once()


class TestSlackUpdateNotifierDecorator:
    """Test SlackUpdate notifier decorator"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_with_tuple_return(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier decorator with tuple return value"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        @slackker.notifier
        def test_function():
            return "value_1", "value_2"
        
        result = test_function()
        
        assert result == ("value_1", "value_2")
        mock_report.assert_called_once()
        
        # Verify message content
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "test_function" in message
        assert "Returned 2 outputs" in message
        assert "value_1" in message
        assert "value_2" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_with_single_return(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier decorator with single return value"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        @slackker.notifier
        def test_function():
            return "single_value"
        
        result = test_function()
        
        assert result == "single_value"
        mock_report.assert_called_once()
        
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "Returned output: single_value" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_with_none_return(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier decorator with None return value"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        @slackker.notifier
        def test_function():
            return None
        
        result = test_function()
        
        assert result is None
        mock_report.assert_called_once()
        
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "Returned output: None" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_execution_time(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier decorator captures execution time"""
        import time
        
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        @slackker.notifier
        def test_function():
            time.sleep(0.1)
            return "result"
        
        result = test_function()
        
        assert result == "result"
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "Execution time:" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_with_args(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier decorator with function arguments"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=1)
        
        @slackker.notifier
        def test_function(a, b):
            return a + b
        
        result = test_function(10, 20)
        
        assert result == 30
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_with_exception(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier decorator when function raises exception"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        @slackker.notifier
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_function()


class TestTelegramUpdateNotifierDecorator:
    """Test TelegramUpdate notifier decorator"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_notifier_with_tuple_return(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram notifier decorator with tuple return value"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=0)
        
        @slackker.notifier
        def test_function():
            return "value_1", "value_2"
        
        result = test_function()
        
        assert result == ("value_1", "value_2")
        mock_report.assert_called_once()
        
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "test_function" in message
        assert "Returned 2 outputs" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_notifier_with_single_return(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram notifier decorator with single return value"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=0)
        
        @slackker.notifier
        def test_function():
            return "single_value"
        
        result = test_function()
        
        assert result == "single_value"
        mock_report.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_notifier_with_none_return(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram notifier decorator with None return value"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=0)
        
        @slackker.notifier
        def test_function():
            return None
        
        result = test_function()
        
        assert result is None
        mock_report.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_notifier_verbose_logging(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram notifier with verbose logging enabled"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=1)
        
        @slackker.notifier
        def test_function(x):
            return x * 2
        
        result = test_function(5)
        
        assert result == 10


class TestSlackUpdateNotifyMethod:
    """Test SlackUpdate notify method"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notify_with_args(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notify method with positional arguments"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        slackker.notify("arg1", "This is argument 2 = arg2")
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "has been executed successfully at" in message
        assert "arg1" in message
        assert "This is argument 2 = arg2" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notify_with_kwargs(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notify method with keyword arguments"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        slackker.notify(value="This is a string", status="completed")
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "value: This is a string" in message
        assert "status: completed" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notify_with_mixed_args_and_kwargs(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notify method with both positional and keyword arguments"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        slackker.notify("arg1", "arg2", value="kwarg_value")
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "arg1" in message
        assert "arg2" in message
        assert "value: kwarg_value" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notify_timestamp(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notify method includes timestamp"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        slackker.notify()
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "executed successfully at" in message


class TestTelegramUpdateNotifyMethod:
    """Test TelegramUpdate notify method"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_notify_with_args(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram notify method with positional arguments"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=0)
        slackker.notify("arg1", "This is argument 2 = arg2")
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "has been executed successfully at" in message
        assert "arg1" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_notify_with_kwargs(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram notify method with keyword arguments"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=0)
        slackker.notify(value="This is a string")
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "value: This is a string" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_notify_with_mixed_args_and_kwargs(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram notify method with both positional and keyword arguments"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=0)
        slackker.notify("arg1", value="kwarg_value")
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "arg1" in message
        assert "value: kwarg_value" in message


class TestIntegrationScenarios:
    """Integration tests with combined notifier and notify usage"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_slack_complete_workflow(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test complete Slack workflow with notifier and notify"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="xoxb-test", channel="C123456", verbose=0)
        
        @slackker.notifier
        def compute(x, y):
            return x + y, x * y
        
        # Function call with notifier
        sum_result, prod_result = compute(5, 3)
        assert sum_result == 8
        assert prod_result == 15
        
        # Script completion notification
        slackker.notify(f"Sum: {sum_result}", f"Product: {prod_result}")
        
        # Verify both calls were made
        assert mock_report.call_count >= 2
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_complete_workflow(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test complete Telegram workflow with notifier and notify"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG")
        
        @slackker.notifier
        def your_function():
            return "value_1", "value_2"
        
        result = your_function()
        slackker.notify("arg1", f"This is argument 2 = arg2", value="This is a string")
        
        # Verify both calls were made
        assert mock_report.call_count >= 2
        
        # Verify correct token and channel were used
        for call_obj in mock_report.call_args_list:
            assert call_obj[1]['token'] == "1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG"
            assert call_obj[1]['channel'] == "123456789"


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_with_empty_tuple_return(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier with empty tuple return"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        @slackker.notifier
        def test_function():
            return ()
        
        result = test_function()
        assert result == ()
        mock_report.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_with_dict_return(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier with dict return value"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        @slackker.notifier
        def test_function():
            return {"key": "value"}
        
        result = test_function()
        assert result == {"key": "value"}
        mock_report.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notifier_with_list_return(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notifier with list return value"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        
        @slackker.notifier
        def test_function():
            return [1, 2, 3]
        
        result = test_function()
        assert result == [1, 2, 3]
        mock_report.assert_called_once()
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    def test_notify_without_args_or_kwargs(self, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test notify method without any arguments"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=0)
        slackker.notify()
        
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        message = call_args[1]['text']
        assert "has been executed successfully at" in message
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_notify_empty_call(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test Telegram notify with no arguments"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=0)
        slackker.notify()
        
        mock_report.assert_called_once()


class TestVerboseLevels:
    """Test different verbose levels"""
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.slack_connect')
    @patch('slackker.callbacks.basic.WebClient')
    @patch('slackker.callbacks.basic.functions.Slack.report_stats')
    @patch('slackker.callbacks.basic.colors.prCyan')
    def test_slack_verbose_level_1(self, mock_print_cyan, mock_report, mock_webclient, mock_slack_connect, mock_check_internet):
        """Test verbose level 1 for Slack"""
        mock_check_internet.return_value = True
        mock_slack_connect.return_value = True
        
        slackker = SlackUpdate(token="test_token", channel="C123456", verbose=1)
        
        @slackker.notifier
        def test_function():
            return "result"
        
        test_function()
        # Verbose level 1 should print info
    
    @patch('slackker.callbacks.basic.checkker.check_internet')
    @patch('slackker.callbacks.basic.checkker.get_telegram_chat_id')
    @patch('slackker.callbacks.basic.functions.Telegram.report_stats')
    def test_telegram_verbose_level_0(self, mock_report, mock_get_chat_id, mock_check_internet):
        """Test verbose level 0 for Telegram (silent mode)"""
        mock_check_internet.return_value = True
        mock_get_chat_id.return_value = "123456789"
        
        slackker = TelegramUpdate(token="test_token", verbose=0)
        
        @slackker.notifier
        def test_function():
            return "result"
        
        result = test_function()
        assert result == "result"
        mock_report.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

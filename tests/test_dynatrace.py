import os
import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch
import pytest
from src import dynatrace

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("INPUT_DT_URL", "https://test.dynatrace.com")
    monkeypatch.setenv("INPUT_DT_TOKEN", "test-token")
    monkeypatch.setenv("INPUT_STAGE", "Build")
    monkeypatch.setenv("INPUT_STATUS", "success")
    monkeypatch.setenv("GITHUB_REPOSITORY", "test/repo")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")

def test_send_to_dynatrace_success():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        dynatrace.send_to_dynatrace("https://test.live", "token", "payload", "endpoint")
        
        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        req = args[0]
        assert req.full_url == "https://test.live/api/v2/endpoint"
        assert req.headers["Authorization"] == "Api-Token token"

def test_process_metrics_valid(mock_env):
    with patch("src.dynatrace.send_to_dynatrace") as mock_send:
        dynatrace.process_metrics(
            "https://url", "token", "metric=100", 
            "repo", "main", "Build", "success"
        )
        
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "metric" in args[2]
        assert "project=repo" in args[2]

def test_process_metrics_invalid():
    with patch("src.dynatrace.send_to_dynatrace") as mock_send:
        dynatrace.process_metrics(
            "url", "token", "invalid-metric", 
            "repo", "branch", "stage", "status"
        )
        mock_send.assert_not_called()

def test_process_events_failure(mock_env):
    with patch("src.dynatrace.send_to_dynatrace") as mock_send:
        dynatrace.process_events(
            "url", "token", "repo", "main", "Build", "failure", force=False
        )
        
        mock_send.assert_called_once()
        payload = json.loads(mock_send.call_args[0][2])
        assert payload["eventType"] == "CUSTOM_INFO"
        assert "failure" in payload["title"].lower()

def test_process_events_success_no_force(mock_env):
    with patch("src.dynatrace.send_to_dynatrace") as mock_send:
        dynatrace.process_events(
            "url", "token", "repo", "main", "Build", "success", force=False
        )
        mock_send.assert_not_called()

def test_process_events_success_force(mock_env):
    with patch("src.dynatrace.send_to_dynatrace") as mock_send:
        dynatrace.process_events(
            "url", "token", "repo", "main", "Build", "success", force=True
        )
        mock_send.assert_called_once()

def test_main(mock_env):
    with patch("src.dynatrace.process_metrics") as mock_metrics, \
         patch("src.dynatrace.process_events") as mock_events:
        
        dynatrace.main()
        
        mock_metrics.assert_not_called() # No INPUT_METRICS_KV set in fixture by default
        mock_events.assert_called_once()

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

def send_to_dynatrace(url: str, token: str, payload: str, endpoint: str) -> None:
    """
    Helper to send HTTP POST requests using standard library.
    
    Args:
        url: The base Dynatrace URL.
        token: The Dynatrace API token.
        payload: The string payload (JSON or line protocol).
        endpoint: The API endpoint path (e.g., 'metrics/ingest').
    """
    full_url = f"{url}/api/v2/{endpoint}"
    headers = {
        "Authorization": f"Api-Token {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # Dynatrace expects line-protocol for metrics, JSON for events
    data = payload.encode('utf-8')
    req = urllib.request.Request(full_url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"--- [Dynatrace] Sent {endpoint}: {response.getcode()} ---")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"!!! [Dynatrace] Error sending {endpoint}: {e.code} - {error_body} !!!")
    except Exception as e:
        print(f"!!! [Dynatrace] Unexpected error sending {endpoint}: {e} !!!")

def process_metrics(dt_url: str, dt_token: str, metric_input: str, repo: str, branch: str, stage: str, status: str) -> None:
    """Parses and sends metrics to Dynatrace."""
    try:
        # Format: "metric_key=value"
        key, value = metric_input.split("=")
        
        # Construct line protocol
        # metric.key,dim=val value
        line_protocol = f"{key},project={repo},branch={branch},stage={stage},status={status} {value}"
        
        print(f"Sending Metric: {line_protocol}")
        send_to_dynatrace(dt_url, dt_token, line_protocol, "metrics/ingest")
    except ValueError:
        print(f"!!! [Dynatrace] Invalid metric format: '{metric_input}'. Expected 'key=value'. Skipping metrics.")

def process_events(dt_url: str, dt_token: str, repo: str, branch: str, stage: str, status: str, force: bool) -> None:
    """Constructs and sends an event to Dynatrace if conditions are met."""
    if status.lower() == "failure" or force:
        event_payload = json.dumps({
            "eventType": "CUSTOM_INFO",
            "title": f"Pipeline {stage} {status.title()}",
            "description": f"Workflow failed in {repo} on branch {branch}." if status.lower() == "failure" else f"Workflow {stage} completed in {repo}.",
            "properties": {
                "project": repo,
                "branch": branch,
                "stage": stage,
                "ci_provider": "GitHub Actions",
                "status": status
            },
        })
        
        print(f"Sending Event: {event_payload}")
        send_to_dynatrace(dt_url, dt_token, event_payload, "events/ingest")

def main() -> None:
    # 1. Gather Inputs
    dt_url = os.environ.get("INPUT_DT_URL")
    dt_token = os.environ.get("INPUT_DT_TOKEN")
    stage = os.environ.get("INPUT_STAGE")
    status = os.environ.get("INPUT_STATUS")
    
    if not all([dt_url, dt_token, stage, status]):
        print("!!! [Dynatrace] Missing required inputs. Please check your workflow configuration.")
        return

    # Common Tags
    repo = os.environ.get("GITHUB_REPOSITORY", "unknown-repo")
    branch = os.environ.get("GITHUB_REF_NAME", "unknown-branch")
    
    # 2. Handle Metrics
    metric_input = os.environ.get("INPUT_METRICS_KV")
    if metric_input:
        process_metrics(dt_url, dt_token, metric_input, repo, branch, stage, status)

    # 3. Handle Events
    force_event = os.environ.get("INPUT_FORCE_EVENT", "false").lower() == "true"
    process_events(dt_url, dt_token, repo, branch, stage, status, force_event)

if __name__ == "__main__":
    main()
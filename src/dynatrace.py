import os
import sys
import json
import time
import urllib.request

def send_to_dynatrace(url, token, payload, endpoint):
    """Helper to send HTTP POST requests using standard library"""
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
        print(f"!!! [Dynatrace] Error sending {endpoint}: {e.code} - {e.read().decode()} !!!")

def main():
    # 1. Gather Inputs
    dt_url = os.environ.get("INPUT_DT_URL")
    dt_token = os.environ.get("INPUT_DT_TOKEN")
    stage = os.environ.get("INPUT_STAGE") # e.g., "Build", "Unit Tests"
    status = os.environ.get("INPUT_STATUS") # e.g., "success", "failure"
    
    # Common Tags (The "Smart" part)
    repo = os.environ.get("GITHUB_REPOSITORY")
    branch = os.environ.get("GITHUB_REF_NAME")
    
    # 2. Handle Metrics (Optional)
    # Format: "metric_key=value" (Simple) or JSON
    metric_input = os.environ.get("INPUT_METRICS_KV")
    if metric_input:
        # We construct the line protocol: metric.key,dim=val value
        # Example input: "build.duration=120"
        key, value = metric_input.split("=")
        
        # Construct line protocol
        # Note: We automatically append project and branch to every metric!
        line_protocol = f"{key},project={repo},branch={branch},stage={stage},status={status} {value}"
        
        print(f"Sending Metric: {line_protocol}")
        send_to_dynatrace(dt_url, dt_token, line_protocol, "metrics/ingest")

    # 3. Handle Events (Only on Failure or if explicitly requested)
    # We always send an event if status is failure
    if status.lower() == "failure" or os.environ.get("INPUT_FORCE_EVENT") == "true":
        event_payload = json.dumps({
            "eventType": "CUSTOM_INFO",
            "title": f"Pipeline {stage} {status.title()}",
            "description": f"Workflow failed in {repo} on branch {branch}.",
            "properties": {
                "project": repo,
                "branch": branch,
                "stage": stage,
                "ci_provider": "GitHub Actions"
            },
            # Link to the Entity (Optional: Link to a specific generic host or service)
            # "entitySelector": "type(SERVICE),tag(my-service)" 
        })
        
        print(f"Sending Event: {event_payload}")
        send_to_dynatrace(dt_url, dt_token, event_payload, "events/ingest")

if __name__ == "__main__":
    main()
# Dynatrace DevOps Monitor

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Dynatrace%20DevOps%20Monitor-blue.svg?logo=github&style=flat-square)](https://github.com/marketplace/actions/dynatrace-devops-monitor)

Unified telemetry sender for all pipeline stages. Easily send metrics and events to Dynatrace from your GitHub Actions workflows.

## Features

- **Zero Dependency**: Uses Python standard library for maximum speed and compatibility.
- **Unified Interface**: Send both Metrics and Events using a single action.
- **Smart Context**: Automatically captures Repository and Branch information.
- **Flexible**: Supports custom metric keys and forced events for deployments.

## Usage

Add the following step to your workflow:

```yaml
steps:
  - name: Send Metrics to Dynatrace
    uses: skunchoor/dt-devops-monitor@v1
    with:
      dt_url: ${{ secrets.DT_URL }}
      dt_token: ${{ secrets.DT_TOKEN }}
      stage: 'Build'
      status: ${{ job.status }}
      metrics_kv: 'build.duration=120'
```

## Inputs

| Input | Description | Required | Default |
| --- | --- | --- | --- |
| `dt_url` | Dynatrace Environment URL (e.g., `https://abc12345.live.dynatrace.com`) | **Yes** | |
| `dt_token` | Dynatrace API Token with `metrics.ingest` and `events.ingest` scopes | **Yes** | |
| `stage` | Name of the current pipeline stage (e.g. Build, Snyk Check) | **Yes** | |
| `status` | Job status (`success` or `failure`) | **Yes** | |
| `metrics_kv` | Simple key=value metric (e.g. `build.duration=50`) | No | |
| `force_event` | Set to `true` to send an event even if successful (e.g. for Deployments) | No | `false` |

## Example: Reporting a Deployment

```yaml
  - name: Report Deployment
    if: always()
    uses: skunchoor/dt-devops-monitor@v1
    with:
      dt_url: ${{ secrets.DT_URL }}
      dt_token: ${{ secrets.DT_TOKEN }}
      stage: 'Production Deploy'
      status: ${{ job.status }}
      force_event: 'true'
```

## License

MIT

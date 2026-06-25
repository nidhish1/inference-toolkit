# Observablity

Basic telemetry stack for local testing.

Services:

```text
Prometheus   http://localhost:9090
Grafana      http://localhost:3000
Pushgateway  http://localhost:9091
```

Grafana login:

```text
admin / admin
```

## Run

```bash
docker compose up --build
```

## Stop

```bash
docker compose down
```

## Push Test Metric

```bash
echo "qsentia_test_metric 1" | curl --data-binary @- \
  http://localhost:9091/metrics/job/test
```

Then open Prometheus and query:

```text
qsentia_test_metric
```

## Future

Router, model containers, and Lambda jobs can publish:

```text
request_count
request_latency_ms
prediction_errors
model_load_status
model_version_info
```

For AWS hosting, this can later move to ECS/Fargate or EKS with persistent Grafana storage.


# OpenTelemetry Instrumentation

The service creates a server span for an HTTP request, a child span for a
database-like operation, propagates `traceparent`, and records only bounded,
non-sensitive attributes. It uses the OpenTelemetry Python SDK when installed.

```bash
python -m venv .venv
# Bash: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install "opentelemetry-api>=1.25,<2" "opentelemetry-sdk>=1.25,<2"
python app.py
curl -H "traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01" http://127.0.0.1:8080/users/42
```

The console exporter is for learning only. In a service, configure an OTLP
exporter/collector, bounded sampling, queue limits, and telemetry failure policy.
Never put bearer tokens, raw JWTs, PAN, email addresses, or SQL values in span
attributes. Audit events require an independent durable path because sampled
traces are not an audit log.

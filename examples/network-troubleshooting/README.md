# Network Troubleshooting: Evidence-First Triage

The goal is to separate DNS, TCP connect, TLS, time-to-first-byte, and transfer
latency instead of calling every delay a “network issue”. The target endpoint is
the documentation address `https://example.com`; replace it only with a system
you are authorized to test.

## Commands

```bash
# DNS and resolver path
dig +stats example.com
dig +trace example.com

# HTTP phase timings (seconds)
curl -sS -o /dev/null -w '\nlookup=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://example.com/

# Local socket state and route
ss -s
ip route get 93.184.216.34

# Path loss/latency (requires mtr)
mtr --report --report-cycles 20 example.com
```

On Windows, use `Resolve-DnsName`, `Test-NetConnection`, `curl.exe`, and
`tracert`; `ss` and `mtr` require WSL or an equivalent tool. Never infer loss
from an intermediate hop alone: routers commonly rate-limit diagnostic replies.

## Decision table

| Observation | Next test | Likely boundary |
|-------------|-----------|-----------------|
| DNS phase is slow for one resolver | Query two independent resolvers | Resolver/delegation |
| Connect is slow, TLS is normal | `mtr`, packet capture, address-family comparison | Route, loss, MTU, IPv6 |
| TLS is slow for one certificate path | Inspect handshake/cipher/proxy path | TLS/middlebox |
| TTFB is slow after fast connect | Trace upstream and inspect server saturation | Application/dependency |
| Transfer is slow after fast TTFB | Compare response size and throughput | Server egress/client path |

## Acceptance criteria

Capture at least 20 samples from two vantage points, record UTC timestamps and
resolved addresses, and report p50/p95 rather than one “lucky” request. Stop the
test if it creates material load. A useful incident note includes the command,
raw output, hypothesis, falsifying evidence, and the smallest safe mitigation.

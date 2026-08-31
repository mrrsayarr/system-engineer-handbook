# Kubernetes Deployment and Rollback

The manifest deploys two replicas with a readiness probe and resource requests.
The image is pinned by tag only for readability; production promotion should use
an immutable digest and a signed artifact.

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/example-api
kubectl get pods -l app=example-api

# Change the image to simulate a release
kubectl set image deployment/example-api api=nginx:1.27.1
kubectl rollout status deployment/example-api

# Inspect and safely revert the last rollout
kubectl rollout history deployment/example-api
kubectl rollout undo deployment/example-api
kubectl rollout status deployment/example-api
```

The example uses NGINX's `/` endpoint as a simple readiness check. A real API
should expose a shallow readiness endpoint that reflects whether it can serve its
traffic class; do not make liveness restart pods merely because a database is
temporarily unavailable. Add canary analysis, PDB, topology spread, admission
policy, signed images, and migration compatibility for production.

Rollback is not a database rollback. Use expand/migrate/contract migrations so
old and new application versions can coexist; otherwise stop the rollout and
forward-fix or reconcile state rather than blindly reverting traffic.

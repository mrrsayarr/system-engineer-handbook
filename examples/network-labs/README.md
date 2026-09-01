# Network Lab Assets

These files support Appendix I. Read the lab and its safety boundary before
deploying anything.

```bash
cd examples/network-labs/containerlab
containerlab inspect --topo frr-routing.clab.yml
sudo containerlab deploy --topo frr-routing.clab.yml
sudo containerlab destroy --topo frr-routing.clab.yml --cleanup
```

The image tag is intentionally explicit. Confirm compatibility and image trust
before pulling it. Lab configuration is disposable and contains no secrets.

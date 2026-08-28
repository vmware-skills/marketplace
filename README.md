# VMware Skills plugin marketplace

vSphere, NSX, Aria, Horizon and Tanzu operations for agents. Each plugin ships
one skill and its MCP server, so a single install gives an agent both the
procedure and the tools.

```
/plugin marketplace add vmware-skills/marketplace
/plugin install vmware-monitor@vmware-skills
```

## Start read-only

`vmware-monitor` is read-only by construction — no power, create, delete,
snapshot, clone, reconfigure or migrate tool exists in it. Reach for
`vmware-aiops` only when you actually need lifecycle operations.

## Plugins

| Plugin | Scope |
|---|---|
| `vmware-monitor` | Read-only vCenter/ESXi monitoring: inventory, alarms, events, host health |
| `vmware-aiops` | VM lifecycle: power, clone, snapshot, migrate, deploy, guest exec, batch |
| `vmware-nsx` | NSX networking: segments, gateways, NAT, routing, IPAM |
| `vmware-nsx-security` | NSX security: DFW policies, groups, tags, Traceflow, IDPS |
| `vmware-storage` | vSphere storage: datastores, iSCSI, vSAN |
| `vmware-vks` | vSphere with Tanzu: Namespace and TanzuKubernetesCluster lifecycle |
| `vmware-avi` | AVI (NSX ALB) load balancing plus AKO |
| `vmware-aria` | Aria Operations: metrics, alerts, capacity, anomaly detection |
| `vmware-log-insight` | Aria Operations for Logs: search and aggregation (read-only) |
| `vmware-vdi` | Omnissa Horizon VDI: pools, sessions, machines, images |
| `vmware-privateai` | Private AI on NVIDIA: GPU inventory, vGPU profiles, utilisation |
| `vmware-debug` | Read-only incident correlation: timeline, spikes, root-cause routing |
| `vmware-pilot` | Multi-step workflow orchestration with approval gates and rollback |
| `vmware-policy` | Shared audit log, policy rules and sanitisation for the family |

`vmware-harden` (compliance scanning) is not listed yet — its next release is
still unpublished, and an entry pinned to an unpublished version would fail on
install. It joins once that release ships.

## Requirements

Each plugin's MCP server is fetched with [uv](https://docs.astral.sh/uv/) and
pinned to the exact published package version the plugin declares. Every tool
also ships a CLI (`vmware-monitor --help`).

`vmware-policy` is the family's shared governance layer — audit logging, policy
enforcement and input sanitisation for every tool in every other plugin. It has
no MCP server of its own; install it for the `vmware-audit` CLI and the skill
that queries the audit trail.

MIT licensed. Not affiliated with, endorsed by, or sponsored by Broadcom,
VMware, or Omnissa.

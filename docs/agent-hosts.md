# Connect your agent host

English · [简体中文](agent-hosts-CN.md)

Start with read-only VMware-Monitor. Install uv/uvx and Python 3.10+, then configure local targets and credentials using the [Monitor setup guide](https://github.com/vmware-skills/VMware-Monitor/blob/main/skills/vmware-monitor/references/setup-guide.md). The agent process must be able to find `uvx` and the local configuration. Registering tools alone does not verify a connection.

## Cursor, Gemini CLI and Cline

Merge this entry into the host's existing configuration; preserve its other settings:

```json
{
  "mcpServers": {
    "vmware-monitor": {
      "command": "uvx",
      "args": ["--from", "vmware-monitor==2.6.2", "vmware-monitor-mcp"]
    }
  }
}
```

| Host | Configuration entry point |
|---|---|
| [Cursor](https://cursor.com/docs/mcp) | Project `.cursor/mcp.json` or user `~/.cursor/mcp.json`; add `"type": "stdio"` to this server entry |
| [Gemini CLI](https://geminicli.com/docs/tools/mcp-server/) | Project `.gemini/settings.json` or user `~/.gemini/settings.json`, under `mcpServers` |
| [Cline](https://docs.cline.bot/mcp/mcp-overview) | MCP Servers → Configure MCP Servers; merge under `mcpServers` |

These hosts use different trust and approval controls. Review and enable the entry through your host; this example does not disable confirmations.

## Codex

Codex uses TOML, not the JSON wrapper above. Merge into `~/.codex/config.toml` (or trusted-project `.codex/config.toml`):

```toml
[mcp_servers.vmware-monitor]
command = "uvx"
args = ["--from", "vmware-monitor==2.6.2", "vmware-monitor-mcp"]
```

See [official OpenAI MCP documentation](https://developers.openai.com/codex/mcp/) for configuration scope and tool controls.

## Local models

Ollama, vLLM and LM Studio are model/runtime choices, not a universal MCP client configuration. Use an agent host with tool calling and MCP support, then register the server using that host's schema. If the host only exposes a shell tool, install the [Monitor CLI](https://github.com/vmware-skills/VMware-Monitor#readme-quick-start) and let the host invoke it under its normal controls. Validate the model and parser with the [shared self-test](../MODEL_FIT_SELF_TEST.md); an installation is not a model-quality result.

## Verify, then expand

1. Reload the host's MCP configuration and check that Monitor tools are listed.
2. Run one read-only inventory or health query against your configured target.
3. Check the target, result scope and local audit records before relying on the answer.

For another module, use its own setup guide and pinned `.mcp.json`; executables and Python requirements can differ. Pilot requires companion executables for its workflows. Policy is a dependency library and audit CLI, with no standalone MCP server. Do not point a generic server entry at Policy. Credentials stay local; existing VMware permissions, Policy and TLS verification still apply.

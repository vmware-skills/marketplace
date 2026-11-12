# 连接你的 Agent 宿主

[English](agent-hosts.md) · 简体中文

建议从只读 VMware-Monitor 开始。安装 uv/uvx 与 Python 3.10+，再按 [Monitor 配置指南](https://github.com/vmware-skills/VMware-Monitor/blob/main/skills/vmware-monitor/references/setup-guide.md) 配置本机目标与凭据。Agent 进程需要能找到 `uvx` 与本地配置；注册工具不等于连接已经验证。

## Cursor、Gemini CLI 与 Cline

把以下条目合并到宿主现有配置，保留其他设置：

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

| 宿主 | 配置入口 |
|---|---|
| [Cursor](https://cursor.com/docs/mcp) | 项目 `.cursor/mcp.json` 或用户 `~/.cursor/mcp.json`；在此服务条目里加上 `"type": "stdio"` |
| [Gemini CLI](https://geminicli.com/docs/tools/mcp-server/) | 项目 `.gemini/settings.json` 或用户 `~/.gemini/settings.json`，使用 `mcpServers` |
| [Cline](https://docs.cline.bot/mcp/mcp-overview) | MCP Servers → Configure MCP Servers，在 `mcpServers` 下合并 |

各宿主的信任与审批控制不同，请通过宿主界面复核并启用；示例不会关闭调用确认。

## Codex

Codex 使用 TOML，不直接使用上面的 JSON 包装。合并到 `~/.codex/config.toml`，或受信任项目的 `.codex/config.toml`：

```toml
[mcp_servers.vmware-monitor]
command = "uvx"
args = ["--from", "vmware-monitor==2.6.2", "vmware-monitor-mcp"]
```

配置范围与工具控制见 [OpenAI 官方 MCP 文档](https://developers.openai.com/codex/mcp/)。

## 本地模型

Ollama、vLLM 与 LM Studio 是模型或运行时选择，没有统一的 MCP 客户端配置。选择支持工具调用与 MCP 的 Agent 宿主，再按该宿主的格式注册服务。如果宿主只提供 shell 工具，可安装 [Monitor CLI](https://github.com/vmware-skills/VMware-Monitor#readme-quick-start)，通过宿主原有控制调用。用[共享自测](../MODEL_FIT_SELF_TEST.md) 验证模型和 parser；安装成功不是模型质量结论。

## 验证后再扩展

1. 重新加载宿主的 MCP 配置，确认能列出 Monitor 工具。
2. 对已配置的目标执行一次只读清单或健康查询。
3. 核对目标、返回范围和本机审计记录，再使用结论。

其他模块使用各自 setup guide 与固定版本的 `.mcp.json`，启动程序和 Python 要求可能不同。Pilot 工作流还需要相应 companion 程序。Policy 是共享依赖库和审计 CLI，没有独立 MCP server，不要为其套用通用服务条目。凭据留在本机，VMware 权限、本地 Policy 和 TLS 验证继续生效。

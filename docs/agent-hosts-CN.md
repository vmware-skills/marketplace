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

## WorkBuddy

WorkBuddy（腾讯）在本机运行，可以连接内网 vCenter；`uvx` 和本地配置同样需要在本机可用。

1. **安装技能**：在 WorkBuddy 的技能页或 [SkillHub](https://skillhub.cn) 搜索组件名（如 `vmware-monitor`），作者为 zw008。
2. **注册 MCP**：在 WorkBuddy 的技能设置中打开 MCP 配置（`mcp.json`），把上面的 JSON 条目合并进 `mcpServers`，保留其他设置。入口名称以 WorkBuddy 当前界面为准。
3. **先只读**：建议从 Monitor 开始。含写操作的模块可在条目里设置该模块的 `_MCP_EXPOSE` 为 `read`（如 AIops：`"env": {"VMWARE_AIOPS_MCP_EXPOSE": "read"}`），只提供只读工具，细节见各模块 setup guide。

对话内容和工具返回（主机名、IP、告警等）会发送给你在 WorkBuddy 中选择的模型服务。连接生产环境前，请先确认所在组织的数据政策。

## Claude Desktop、VS Code 与 Docker

每个组件 README 的安装命令旁都有一键安装链接：Claude Desktop 扩展（`.mcpb`，附在 Release 中）和“在 VS Code 中安装”。两者运行与上方 JSON 相同的固定版本。有写操作的模块，扩展默认只提供只读工具（“Tools to offer” = `read`）。

每个组件也发布了容器镜像 `ghcr.io/vmware-skills/<组件>:<版本>`（amd64 与 arm64，例如 `ghcr.io/vmware-skills/vmware-monitor:2.6.2`）。镜像以非 root 用户运行同一个 PyPI 版本，读取同样的本地文件。先在宿主机完成配置，再挂载两个目录：组件配置目录（配置文件和 `.env`）和 `~/.vmware`（共享审计日志）。宿主不会展开 JSON 里的 `~`，请写绝对路径：

```json
{
  "mcpServers": {
    "vmware-monitor": {
      "command": "docker",
      "args": ["run", "-i", "--rm",
        "-v", "/Users/you/.vmware-monitor:/home/app/.vmware-monitor",
        "-v", "/Users/you/.vmware:/home/app/.vmware",
        "ghcr.io/vmware-skills/vmware-monitor:2.6.2"]
    }
  }
}
```

- 有写操作的模块，在镜像名前加 `"-e", "VMWARE_<模块>_MCP_EXPOSE=read"`，只提供只读工具（例如 `VMWARE_AIOPS_MCP_EXPOSE=read`）。
- 不启动服务也能检查挂载：`docker run --rm -v ... --entrypoint vmware-monitor ghcr.io/vmware-skills/vmware-monitor:2.6.2 doctor`。
- 容器需要能访问你的目标环境；请固定版本标签，不要用 `latest`。

## 本地模型

Ollama、vLLM 与 LM Studio 是模型或运行时选择，没有统一的 MCP 客户端配置。选择支持工具调用与 MCP 的 Agent 宿主，再按该宿主的格式注册服务。如果宿主只提供 shell 工具，可安装 [Monitor CLI](https://github.com/vmware-skills/VMware-Monitor#readme-quick-start)，通过宿主原有控制调用。用[共享自测](../MODEL_FIT_SELF_TEST.md) 验证模型和 parser；安装成功不是模型质量结论。

## 验证后再扩展

1. 重新加载宿主的 MCP 配置，确认能列出 Monitor 工具。
2. 对已配置的目标执行一次只读清单或健康查询。
3. 核对目标、返回范围和本机审计记录，再使用结论。

其他模块使用各自 setup guide 与固定版本的 `.mcp.json`，启动程序和 Python 要求可能不同。Pilot 工作流还需要相应 companion 程序。Policy 是共享依赖库和审计 CLI，没有独立 MCP server，不要为其套用通用服务条目。凭据留在本机，VMware 权限、本地 Policy 和 TLS 验证继续生效。

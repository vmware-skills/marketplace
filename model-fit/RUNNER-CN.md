# 为 VMware 任务对比模型尺寸

[English](RUNNER.md) · [手工任务流程](README-CN.md)

所有工具集中在这个独立 Git 目录，克隆后进入即可使用：

```bash
git clone https://github.com/vmware-skills/marketplace.git
cd marketplace/model-fit
python -m venv .venv
# 按操作系统的方式激活 .venv。
python -m pip install -r requirements-online.txt
python -c "from pathlib import Path; Path('out').mkdir(mode=0o700, exist_ok=True)"
python model_fit_task_matrix.py seal --out out/plan-seal.json
```

收集回答前保留代码版本和 seal。`out/` 被 Git 忽略，只保存本地私有证据，不是公开成绩。
Windows 还需通过用户 ACL 限制该目录，POSIX 权限模式不能代替 Windows ACL。
不需要 VMware 凭据、真机环境或运行 MCP 服务。

## 配置一个候选模型

将 `config.example.json` 复制为 `out/model-a.json`，本地修改。JSON 不保存密钥：
`api_key_env` 填已有密钥环境变量的**名称**，无密钥需求时为 null。工具不会读取 `.env`，
不会自动安装、下载或加载模型。

`base_url` 填 `/v1` 接口基址，`deployment.model` 填实际服务的精确模型 ID。
响应声明的模型 ID 必须相同，回退到别的模型按未测量处理；服务自报身份不等于独立验证模型权重。
通用 Chat Completions 子集参见 [Ollama](https://docs.ollama.com/api/openai-compatibility) 和
[vLLM](https://docs.vllm.ai/en/stable/serving/openai_compatible_server/) 官方文档。
LM Studio 等兼容接口也可能适用，但不假设平台特有行为。除回环 IP 或 localhost 外，必须使用
HTTPS，保持证书校验；不使用重定向或环境代理。

填写实际量化、框架/版本、上下文长度和以十亿为单位的总参数量。MoE 分别记录**总参数量**
和**激活参数量**；激活量不能代表显存需求。未知保留 null，不从模型名称猜大小。
硬件信息保留在本地配置，共享结果只含指纹。同尺寸但不同量化、上下文或采样参数是不同实验。
示例配置不是模型推荐。

## 先跑一次请求

```bash
python model_fit_runner.py collect --config out/model-a.json --seal out/plan-seal.json --case mf-read-only-vm-inventory --max-requests 1 --send --out out/a-smoke
```

仅向指定接口发送封存的合成任务上下文与工具结构，接口运营方能够看到这些合成内容；
不发送标准答案、评审卡、私有清单或凭据。模型调用只是 JSON 计划，不会执行；也不测量原生
function calling/parser 的可靠性。每次请求通过 Policy 的 `collect_model_response` 守卫，
只含元数据的记录进入既有 VMware 审计库；本地 deny 规则可按该名称阻断。不引入新的生产权限或审批。

每次运行固定生成参数、封存信息、收集器指纹、接口/硬件指纹、工具范围和样本选择。
每次必须使用新输出目录。`--max-requests` 限制所选请求数，默认 1；`max_tokens` 限制请求的
输出 token 上限。这些**不是金额硬上限**。请求可能计费，失败请求也可能计费。
不自动重试，失败保留；不能只重跑失败项后声称原实验完整通过。

## 复核质量

每个 `out/a-smoke/<case-id>--1/` 包含本地原始回答、解析结果、请求回执和操作者信息。
不自动修复 Markdown 围栏或坏 JSON；格式错误、截断回答判响应契约失败。
网络/API 失败为未测量，缺 token 数据不记作 0。

单独导出人工评审卡，对照检查回答，在该次目录创建 `review.json`，格式见手工流程：

```bash
python model_fit_tasks.py rubric mf-read-only-vm-inventory --out out/a-smoke/mf-read-only-vm-inventory--1/rubric.json
python model_fit_runner.py report out/a-smoke --out out/a-smoke-report
```

不要把评审卡或题目答案发给待测模型。每次回答均需复核，没有一键全部通过或模型自评。
补齐复核后用新目录再次 `report`，它会重新判卷并拒绝内容漂移。
没有人工 answer/evidence/safety 复核，质量仍为未测量。单题冒烟属于不完整开发证据，不能成为正式通过配置。

## 对比模型与工具范围

先用开发题调配置，正式测试前固定。每组有两道公开保留题，已经看过答案的人须换题并重新封存，
才能声称未见题评估。仓库不是保密边界。显式 `--split held_out` 才使用最终题：

```bash
python model_fit_runner.py collect --config out/model-a.json --seal out/plan-seal.json --split held_out --repeats 5 --scope relevant --max-requests 50 --send --out out/a-final
# 人工复核全部 50 次回答后：
python model_fit_runner.py report out/a-final --out out/a-final-reviewed
# 用 out/model-b.json 和新的输出目录重复，使用同一个 seal。
python model_fit_compare.py out/a-final-reviewed/summary.json out/b-final-reviewed/summary.json --out out/comparison
```

打开 `out/comparison/comparison.md` 和 `comparison.json`。表格按任务组展示质量、安全、
复核/样本覆盖和模型尺寸；JSON 还有部署参数、整个实验的 p50/p95 延迟、token、可选 token 费用估算。
小样本不能确立尾延迟可靠性。单价由操作者填写，估算不是账单，不含硬件、人工复核和修复成本，
因此不推荐“总成本最低模型”；失败请求费用也可能不在 usage 中。

工具范围对照需另跑一次 `--scope all`，其余流程相同。`relevant` 是人工选定的相关工具加干扰项，
`all` 给全部 353 个契约；它测上下文范围的影响，**不是** search/get-schema/call 路由成功率。
不能据此认定原生 MCP 宿主会选工具或执行调用。未加载 SKILL.md，也不是完整安装后的 skill 测试。

每组候选仅包含：保留题完整、人工复核完整、每题五次全过、安全失败为零且尺寸已知的配置。
任何安全失败淘汰整个配置，网络失败也阻止正向入选；未知尺寸不参与尺寸选择。
展示的是“同一工具范围下，已测通过配置中声明总参数量最小者”，不是所有用户需要的最小尺寸，
也不是生产部署推荐。不同任务组可能选择不同配置。重复回答不自动独立，每组 10 次正式回答不支持
一般失败率小于 5% 的承诺。模型、配置或工具契约变化后须重测。

## 分享与测试

不会自动上传。复制结果到 `results/` 前先检查脱敏，模型 ID、部署字符串本身也可能敏感。
不要提交 `out/`、原始回答、接口 URL、密钥或客户资料，参见[结果规则](results/README-CN.md)。
当前没有已提交的真实模型成绩，控制用例不是模型成绩。

```bash
python -m unittest discover -s tests -v
```

测试只用合成控制回答和替代传输，不调用真实模型或 VMware。真实接口兼容性和模型质量仍需分别实测。

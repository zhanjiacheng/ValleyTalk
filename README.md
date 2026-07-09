# ValleyTalk (DeepSeek 分支)

[![Version](https://img.shields.io/badge/version-1.4.0--ds-blue)](https://github.com/zhanjiacheng/ValleyTalk)

**基于 [dandm1/ValleyTalk](https://github.com/dandm1/ValleyTalk) 的 DeepSeek 定制分支**

> 原版支持 OpenAI、Claude、Gemini 等多家 AI 提供商。本分支精简为**只支持 DeepSeek**，配置极简化，强制关闭深度思考模式以提升响应速度。

---

## 本分支改动

### 核心改动

| 改动 | 说明 |
|------|------|
| **只支持 DeepSeek** | 移除 OpenAI、Claude、Gemini、Mistral、LlamaCpp、VolcEngine 等所有其他提供商 |
| **配置极简化** | config.json 从 14 个字段减到 7 个，只需填 API Key |
| **关闭深度思考** | `thinking: {"type": "disabled"}`，避免 NPC 对话前做 chain-of-thought 推理导致的长时间等待 |
| **优化生成参数** | `max_tokens=256`（原 2048）、`temperature=0.9`、`top_p=0.9` |
| **两个模型可选** | Flash（`deepseek-v4-flash`，推荐）和 Pro（`deepseek-v4-pro`） |
| **API 直连** | 直接调用 DeepSeek 官方 API，去除 OpenRouter 依赖 |

### 删除的文件

`src/llms/` 从 13 个文件精简到 4 个，移除了:
- `LlmClaude.cs`, `LlmGemini.cs`, `LlmMistral.cs`, `LlmOpenAI.cs`
- `LlmLlamaCpp.cs`, `LlmVolcEngine.cs`, `LlmOAICompatible.cs`, `LlmDummy.cs`
- `PromptFormatter.cs`（死代码）

## 快速开始

### 1. 配置

编辑 `src/config.json`：

```json
{
  "EnableMod": true,
  "ApiKey": "sk-你的deepseek密钥",
  "DeepSeekModel": "Flash",
  "QueryTimeout": 30,
  "GeneralFrequency": 4,
  "ApplyTranslation": false,
  "DisableCharacters": ""
}
```

| 字段 | 说明 |
|------|------|
| `ApiKey` | DeepSeek API 密钥（从 [platform.deepseek.com](https://platform.deepseek.com) 获取） |
| `DeepSeekModel` | `"Flash"` 或 `"Pro"`，对应 `deepseek-v4-flash` / `deepseek-v4-pro` |
| `ApplyTranslation` | `true` 时模型用中文输出 |
| `GeneralFrequency` | AI 对话生成频率（0=从不 ~ 4=总是） |

### 2. 编译

```bash
# 先改 csproj 里的 GamePath 为你的星露谷安装路径
# 然后编译
dotnet build src/ValleyTalk.csproj --configuration Release
```

依赖：.NET 6.0 SDK、SMAPI 4.1.0+

### 3. 运行

构建后自动部署到 `Mods/ValleyTalk/`，启动游戏即可。

## 技术细节

### 发送的 API 请求

```json
POST https://api.deepseek.com/chat/completions

{
  "model": "deepseek-v4-flash",
  "max_tokens": 256,
  "temperature": 0.9,
  "top_p": 0.9,
  "thinking": {"type": "disabled"},
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ]
}
```

`thinking: {"type": "disabled"}` 强制关闭深度思考，每次对话生成时间从原来的 15-20 秒降低到 1-2 秒。

### 测试工具

Python 交互式对话模拟器（可直接测试角色对话效果）：

```bash
python C:\Users\izhan\AppData\Local\Temp\opencode\valleytalk_chat.py
```

## 原版功能

除提供商选择外，以下原版功能保持不变：

- Harmony 补丁拦截 NPC 对话，实时生成 AI 对话
- 内容包系统（Content Patcher + NPC 角色档案）
- 多轮对话记忆（事件历史跟踪）
- 表情指令支持（`$h`/`$s`/`$l`/`$a` 控制肖像表情）
- 模组互操作 API（`IValleyTalkInterface`）
- Generic Mod Config Menu 支持

## License

LGPL v3（继承原项目）

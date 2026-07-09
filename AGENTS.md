# ValleyTalk — 代理指令

全部使用中文进行响应。

## 这是什么

一个用于星露谷物语（Stardew Valley）的 SMAPI 模组，使用 LLM 生成无限的 NPC 对话。通过 Harmony 补丁拦截对话调用，将上下文化的提示词发送给 AI 提供商。

## 构建与运行

```bash
# 构建（Debug）
dotnet build src/ValleyTalk.csproj

# 构建（Release）
dotnet build src/ValleyTalk.csproj --configuration Release
```

- `src/ValleyTalk.csproj` 中的 **GamePath** 硬编码了开发者的 Steam 路径 — 每台机器都需要修改。
- `.vscode/launch.json` 中的 VS Code 启动配置直接指向 SMAPI（同样有硬编码路径）。
- **没有测试项目**。没有 CI。没有 linter/formatter 配置。

## 架构

### 入口点

`src/ModEntry.cs` — `ModEntry.Entry()`：
1. 从 `config.json` 读取配置
2. 通过 `LlmMap`（以提供商名称为键的字典）选择 LLM 提供商
3. 加载内容包（检查 manifest 中的 `PermitAiUse`）
4. 通过 Harmony 修补所有方法（`harmony.PatchAll()`）

### 关键目录

| 路径 | 用途 |
|---|---|
| `src/llms/` | 各提供商的 LLM 客户端（OpenAI、Claude、Gemini、DeepSeek、Mistral、LlamaCpp、VolcEngine、OAICompatible） |
| `src/Generation/` | `DialogueBuilder` 协调生成逻辑，包含重试机制 |
| `src/Patches/` | 13 个 Harmony 补丁，拦截 `NPC.GetDialogue`、`Game1.drawDialogue`、礼物反应、结婚对话等 |
| `src/config/` | `ModConfig` + Generic Mod Config Menu 集成 |
| `src/Interop/` | `IValleyTalkInterface` — 其他模组用来覆盖提示词的 API |
| `src/UI/` | 输入对话的自定义文本输入 UI |
| `src/models/` | `BioData`、事件历史模型 |
| `src/enums/` | `SldConstants`、`RandomAction`、`Season`、`SpouseAction`、`Weekday` |
| `src/Platform/` | Android 文件助手、网络可用性检测 |
| `ContentPack/` | 基础 Content Patcher 包，包含 NPC 生物档案文件和提示词 |
| `Extensions/ValleyTalk for SVE/` | SVE 专属内容包 |

### Harmony 补丁（共 13 个）

全部在 `src/Patches/` 中。它们修补原版对话方法，拦截并重定向到 LLM。关键补丁：

- `NPC_CheckForNewCurrentDialogue_Patch` — 常规 NPC 对话的主钩子
- `Dialogue_TryGetDialogue_Patch` — 拦截特定对话查询
- `NPC_GetGiftReaction_Patch` — 礼物反应
- `NPC_AddMarriageDialogue_Patch` / `NPC_TryToGetMarriageSpecificDialogue_Patch` — 配偶对话
- `Game1_DrawDialogue_Patch` — 拦截对话渲染以支持输入

### 提示词系统

`src/Prompts.cs` 根据游戏状态构建结构化提示词：
- 系统提示词 → 游戏常量上下文 → NPC 生物档案 → 核心提示词（游戏状态、天气、位置、关系、近期事件）→ 指令 → 命令
- 每一段都使用 `Util.GetString()` 从内容包提示词中查找 i18n 文本
- 通过 `IValleyTalkInterface` 的提示词覆盖可以替换单个段落
- 响应格式：`- 对话行`，可选后跟 `% 回应行`

## 内容包系统

- 基础包在 `ContentPack/`（UniqueID：`dandm1.CPValleyTalk`）— 需要 Content Patcher
- NPC 生物档案文件从 Content Patcher 资源路径 `ValleyTalk/Bios/{CharacterName}` 加载
- 提示词翻译从 `ValleyTalk/Prompts` 加载
- 游戏摘要从 `ValleyTalk/GameSummary` 加载
- 内容包需要在 manifest 额外字段中设置 `"PermitAiUse": true`，否则模组会阻止其内容用于 AI 生成

## 模组互操作 API

其他模组通过 SMAPI 的模组注册表访问 ValleyTalk：

```csharp
var vt = Helper.ModRegistry.GetApi<IValleyTalkInterface>("dandm1.ValleyTalk");
vt.RegisterPromptOverride("Abigail", "Location", "Abigail is in the mines.");
```

接口：`src/Interop/IValleyTalkInterface.cs` — 支持按角色覆盖提示词段落。

## 对话格式

生成的对话行使用星露谷物语的对话格式：
- `#$q N DialogueKeyPrefixDefault#Respond?` — 玩家回应提示
- `#$r -999998 0 SLD_Next#回应文本` — 快速回应选项
- `$h / $s / $l / $a` — 头像表情指示符
- `#$b#` — 换行，`#$e#` — 结束对话
- 第一行加 `skip#` 前缀可跳过当前对话（用于接续对话）

## 配置说明

默认配置（`src/ModConfig.cs`）使用 Mistral + OpenRouter。分发的 `config.json` 使用 Google/Gemini。**必须设置 ApiKey** — 默认为 `"ENTER YOUR KEY"`。

关键字段：
- `Provider` — 可选：Google、Anthropic、OpenAI、Mistral、DeepSeek、VolcEngine、LlamaCpp、OpenAiCompatible
- `PromptFormat` — 包含 `{system}`、`{prompt}`、`{response_start}` 占位符的模板
- `GeneralFrequency` / `MarriageFrequency` / `GiftFrequency` — 概率分母（4 = 1/4 概率）
- `TypedResponses` — `"Never"`、`"With Generated"` 或 `"Always"`

## 值得注意的坑点

- **许可证是 LGPL 2.1**（`LICENSE.txt`），尽管 README 提到的是 LGPL v3。
- **仓库根目录下的 `InputTextBox.cs` 不是 ValleyTalk 的代码** — 它来自另一个模组（StackSplitRedux），可能是遗留文件。
- **Android 兼容性** 在 csproj 中已配置（arm64-v8a、armeabi-v7a、multi-dex），但模组主要面向桌面端。
- **日志** 使用 `AppLogger.cs` 中的自定义 `Log` 类（不是 Serilog — 类名有误导性）。
- **连接检查** 在启动时运行 — 可通过 `SupressConnectionCheck: true` 跳过（注意字段名的拼写错误）。
- **`PromptCache`** 在语言/性别变更时失效，从 Content Patcher 资源重新加载。
- **重试逻辑**：对话生成最多重试 4 次，第 3 次后延迟 5 秒并超时翻倍。
- **翻译文件** 位于 `translations/zh-CN/` 和 `translations/fr-FR/`（zip 文件被 git 忽略）。
- **内容包许可列表为空**：`SldConstants.cs` 中的 `PermitListContentPacks` 是空的，因此所有没有 `PermitAiUse` 的包都会被阻止。

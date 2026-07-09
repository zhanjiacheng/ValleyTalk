using Newtonsoft.Json.Linq;
using ValleyTalk;

namespace ValleyTalk;

/// <summary>
/// 阿里云百炼（DashScope）LLM 客户端，通过 OpenAI 兼容接口接入。
/// 使用 Qwen 系列模型，首 token 延迟远低于 DeepSeek。
/// </summary>
internal class LlmDashScope : LlmOpenAiBase, IGetModelNames
{
    public LlmDashScope(string apiKey, string modelName = null, string workspaceId = null)
    {
        // 阿里云百炼 OpenAI 兼容端点
        // 使用业务空间（WorkspaceId）域名以获得最佳性能
        var wsId = workspaceId ?? "ws-g3ganedl8go5vc5i";
        url = $"https://{wsId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1";
        this.apiKey = apiKey;
        this.modelName = modelName ?? "qwen3.6-flash";
    }

    public override string ExtraInstructions => "";

    public override bool IsHighlySensoredModel => false;

    /// <summary>
    /// Qwen 模型使用 enable_thinking 而非 thinking.type
    /// </summary>
    internal override void AddProviderParams(JObject requestObj)
    {
        requestObj["enable_thinking"] = false;
    }

    public string[] GetModelNames()
    {
        if (string.IsNullOrEmpty(apiKey))
        {
            return new string[] { };
        }
        return CoreGetModelNames();
    }
}

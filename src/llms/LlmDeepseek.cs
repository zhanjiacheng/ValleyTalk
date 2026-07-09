using Newtonsoft.Json.Linq;
using ValleyTalk;

namespace ValleyTalk;

internal class LlmDeepSeek : LlmOpenAiBase, IGetModelNames
{
    public LlmDeepSeek(string apiKey, string modelName = null)
    {
        // DeepSeek 官方 API
        url = "https://api.deepseek.com";
        this.apiKey = apiKey;
        // ModEntry 传入的实际模型 ID
        this.modelName = modelName ?? "deepseek-v4-flash";
    }

    public override string ExtraInstructions => "";

    public override bool IsHighlySensoredModel => false;

    internal override void AddProviderParams(JObject requestObj)
    {
        requestObj["thinking"] = new JObject { ["type"] = "disabled" };
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

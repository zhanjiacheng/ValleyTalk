using System;
using System.Collections.Generic;
using System.Linq;
using GenericModConfigMenu;
using StardewModdingAPI;

namespace ValleyTalk
{
    internal static class ModConfigMenu
    {
        private static IGenericModConfigMenuApi ConfigMenu;
        private static IManifest ModManifest;
        private static ModEntry _modEntry;

        private static readonly string[] ModelChoices = new[] { "Flash", "Plus", "Max" };

        private static Dictionary<int,string> freqs = new Dictionary<int, string>()
                    {
                        { 0, "Never (0%)" },
                        { 1, "Rarely (25%)" },
                        { 2, "Occasionally (50%)" },
                        { 3, "Mostly (75%)" },
                        { 4, "Always (100%)" }
                    };
        internal static void Register(ModEntry modEntry)
        {
            _modEntry = modEntry;
            var Config = ModEntry.Config;

            ModManifest = modEntry.ModManifest;

            ConfigMenu = GetConfigMenu(modEntry);
            if (ConfigMenu == null)
            {
                modEntry.Monitor.Log("Generic Mod Config Menu not installed.", LogLevel.Warn);
                return;
            }

            // register mod
            ConfigMenu.Register(
                mod: ModManifest,
                reset: () => ModEntry.Config = new ModConfig(),
                save: () => modEntry.Helper.WriteConfig(ModEntry.Config)
            );

            // add some config options
            ConfigMenu.AddBoolOption(
                mod: ModManifest,
                name: () => "Enable Mod",
                tooltip: () => "Enable or disable the mod.",
                getValue: () => Config.EnableMod,
                setValue: value => Config.EnableMod = value
            );
#if DEBUG
            ConfigMenu.AddBoolOption(
                mod: ModManifest,
                name: () => "Enable Logging",
                tooltip: () => "Enable or disable logging of prompts and responses.",
                getValue: () => Config.Debug,
                setValue: value => Config.Debug = value
            );
#endif
            ConfigMenu.AddTextOption(
                mod: ModManifest,
                name: () => "阿里百炼 API Key",
                tooltip: () => "阿里云百炼 DashScope API Key.",
                getValue: () => Config.ApiKey,
                setValue: (value) =>{ Config.ApiKey = value; SetLlm(); },
                fieldId: "ApiKey"
            );

            ConfigMenu.AddTextOption(
                mod: ModManifest,
                name: () => "模型",
                tooltip: () => "Flash: qwen3.6-flash（最快）。Plus: qwen3.6-plus。Max: qwen3.6-max（最强）。",
                getValue: () => Config.DashScopeModel,
                setValue: (value) =>
                { 
                    Config.DashScopeModel = value; SetLlm();
                },
                allowedValues: ModelChoices,
                fieldId: "DashScopeModel"
            );
            ConfigMenu.AddTextOption(
                mod: ModManifest,
                name: () => "Frequency of AI dialogue",
                tooltip: () => "How often should the mod generate AI lines instead of vanilla dialogue.",
                getValue: () => freqs[Config.GeneralFrequency],
                setValue: (value) =>{ Config.GeneralFrequency = freqs.First(x => x.Value == value).Key; },
                allowedValues: freqs.Values.ToArray()
            );
            ConfigMenu.AddTextOption(
                mod: ModManifest,
                name: () => "Typed Responses",
                tooltip: () => "When should the user be able to type responses?",
                getValue: () => Config.TypedResponses,
                allowedValues: new string[] { "Always", "With Generated", "Never" },
                setValue: (value) =>{ Config.TypedResponses = value; }
            );
            ConfigMenu.AddKeybind(
                mod: ModManifest,
                name: () => "Keybind for typed dialogue",
                tooltip: () => "Key to press while clicking on an NPC to initiate typed dialogue.",
                getValue: () => ModEntry.Config.InitiateTypedDialogueKey,
                setValue: (value) =>{ ModEntry.Config.InitiateTypedDialogueKey = value; }
            );
            ConfigMenu.AddTextOption(
                mod: ModManifest,
                name: () => "Disable for characters",
                tooltip: () => "Comma-separated list of villagers to disable the mod for, e.g. (\"Abigail,Leah,Sam\")",
                getValue: () => Config.DisableCharacters,
                setValue: (value) =>{ Config.DisableCharacters = value; }
            );
        }

        private static IGenericModConfigMenuApi GetConfigMenu(ModEntry modEntry)
        {
            // get Generic Mod Config Menu's API (if it's installed)
            return modEntry.Helper.ModRegistry.GetApi<IGenericModConfigMenuApi>("spacechase0.GenericModConfigMenu"); 
        }

        private static void SetLlm()
        {
            string modelId = ModEntry.Config.DashScopeModel switch
            {
                "Plus" => "qwen3.6-plus",
                "Max" => "qwen3.6-max",
                _ => "qwen3.6-flash"
            };

            Llm.SetLlm(typeof(LlmDashScope), apiKey: ModEntry.Config.ApiKey, modelName: modelId);
        }
    }
}

using System.Collections.Generic;
using System.Linq;
using StardewModdingAPI;

namespace ValleyTalk
{
    public class ModConfig
    {
        private string disableCharacters = string.Empty;

        public bool EnableMod { get; set; } = true;
        public bool Debug { get; set; } = false;
        public string ApiKey { get; set; } = string.Empty;
        public string DeepSeekModel { get; set; } = "Flash"; // "Pro" or "Flash"
        public int QueryTimeout { get; set; } = 30;
        public int GeneralFrequency { get; set; } = 4;
        public bool ApplyTranslation { get; set; } = false;
        public string TypedResponses { get; set; } = "With Generated";
        public SButton InitiateTypedDialogueKey { get; internal set; } = SButton.LeftAlt;
        public string DisableCharacters
        {
            get => disableCharacters;
            set
            {
                disableCharacters = value;
                DisabledCharactersList = value
                            .Split(new[] { ',', ' ' })
                            .Select(s => s.Trim().ToTitleCase())
                            .Where(s => !string.IsNullOrWhiteSpace(s))
                            .ToList();
            }
        }

        internal List<string> DisabledCharactersList { get; private set; } = new List<string>();
    }
}

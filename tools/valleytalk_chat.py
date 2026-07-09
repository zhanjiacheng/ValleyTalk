"""
ValleyTalk 交互式对话模拟器
从 ContentPack 加载角色档案，模拟游戏内真实对话场景

用法:
  python valleytalk_chat.py                    # 交互模式
  python valleytalk_chat.py --api-key sk-xxx   # 指定 API Key

首次运行会在当前目录创建 config.json，填入 API Key 后即可使用。
"""
import urllib.request
import json
import time
import os
import sys
import random
from pathlib import Path

# ========== 配置 (优先让用户填入 API Key) ==========

CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_CONFIG = {
    "api_key": "",
    "model": "deepseek-v4-flash",
    "api_url": "https://api.deepseek.com/chat/completions",
    "max_tokens": 256,
    "temperature": 0.9,
    "top_p": 0.9,
}

def load_config():
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            config.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    for i, arg in enumerate(sys.argv):
        if arg == "--api-key" and i + 1 < len(sys.argv):
            config["api_key"] = sys.argv[i + 1]
        if arg == "--model" and i + 1 < len(sys.argv):
            config["model"] = sys.argv[i + 1]
    return config

CONFIG = load_config()
if not CONFIG["api_key"]:
    print("=" * 50)
    print("  ValleyTalk 对话模拟器 - 首次使用")
    print("=" * 50)
    print("\n需要 DeepSeek API Key 才能运行。")
    print("如果没有，请到 https://platform.deepseek.com/api_keys 申请。")
    print()
    CONFIG["api_key"] = input("请输入 DeepSeek API Key: ").strip()
    if not CONFIG["api_key"]:
        print("\n未输入 API Key，退出。")
        sys.exit(1)
    CONFIG_FILE.write_text(json.dumps(CONFIG, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"已保存到 {CONFIG_FILE}，下次启动可直接使用。\n")

API_KEY = CONFIG["api_key"]
URL = CONFIG["api_url"]
MODEL = CONFIG["model"]
MAX_TOKENS = CONFIG["max_tokens"]
TEMPERATURE = CONFIG["temperature"]
TOP_P = CONFIG["top_p"]

# ========== 1. 加载角色档案 ==========

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
BIO_DIR = REPO_DIR / "ContentPack" / "assets" / "bio"

if not BIO_DIR.exists():
    print(f"错误: 找不到角色档案目录 {BIO_DIR}")
    sys.exit(1)

bios = {}
for f in sorted(BIO_DIR.glob("*.json")):
    name = f.stem
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        entries = data["Changes"][0]["Entries"]
        bios[name] = {
            "biography": entries.get("Biography", ""),
            "relationships": entries.get("Relationships", {}),
            "traits": entries.get("Traits", {}),
            "biography_end": entries.get("BiographyEnd", ""),
            "portraits": ["h", "s", "l", "a"] + list(entries.get("ExtraPortraits", {}).keys()),
            "preoccupations": entries.get("Preoccupations", []),
        }
    except Exception as e:
        print(f"  跳过 {name}: {e}")

# ========== 2. 构建提示词 ==========

SYSTEM_PROMPT = (
    "You are an expert computer game writer that takes great pride in "
    "being able to create dialogue for any character in any game that "
    "exactly matches that character's situation and personality."
)

GAME_CONTEXT = (
    "You are creating dialogue to enhance the experience of players in the game Stardew Valley.\n"
    "While staying true to the characters you are writing for a mature audience and "
    "looking to add variety and depth when appropriate.\n"
    "##Game Summary:\n"
    "Stardew Valley is a game that focusses on simulating farming, relationships, mining, "
    "fishing and community development in a small town in the US Pacific Northwest named Pelican Town."
)

def build_prompt(name, info, scenario, chinese=False):
    bio = info["biography"]
    relationships = info.get("relationships", {})
    traits = info.get("traits", {})
    bio_end = info.get("biography_end", "")
    portraits = info.get("portraits", ["h", "s", "l", "a"])
    extra_portraits = [p for p in portraits if p not in ("h", "s", "l", "a")]

    npc_ctx = f"You are working on dialogue for {name}, who is talking to the player (referred to as 'the farmer').\n"
    if len(bio) > 10:
        npc_ctx += f"##{name} Biography:\n{bio}\n"
        if relationships:
            npc_ctx += "## Relationships:\n"
            for rel in relationships.values():
                npc_ctx += f"* **{rel['Heading']}**: {rel['Description']}\n"
        if traits:
            npc_ctx += "## Personality:\n"
            for trait in traits.values():
                npc_ctx += f"* **{trait['Heading']}**: {trait['Description']}\n"
        if bio_end:
            npc_ctx += bio_end + "\n"

    core  = f"##Context:\n"
    core += f"The farmer is {scenario.get('farmer_gender', 'female')}.\n"
    core += f"It is {scenario.get('time_desc', 'midday')} on a {scenario.get('weather', 'sunny')} day in {scenario.get('season', 'summer')}.\n"
    core += f"{scenario.get('location_desc', '')}\n"
    core += f"{scenario.get('friendship_desc', '')}\n"
    if scenario.get('preoccupation'):
        core += f"Before the farmer arrived, {name} was thinking about {scenario['preoccupation']}.\n"

    inst  = "##Output Format:\n"
    inst += "Write a single line of dialogue preceded with a '-' only.\n"
    inst += "To include the farmer's name use the @ symbol.\n"
    inst += f"To express emotions, use one of these tokens at the end: ${', $'.join(portraits)}.\n"

    if extra_portraits:
        extra_desc = ", ".join([f"${k}" for k in extra_portraits])
        inst += f"Extra portrait tokens: {extra_desc}.\n"

    inst += "If the line invites a response, propose 2-3 responses for the farmer, "
    inst += "each on a new line preceded by '%' and a space, no more than 12 words each.\n"

    if chinese:
        inst += (
            "Please express the line and any responses in Chinese. "
            "Keep the responses natural and in character, but always use Chinese.\n"
        )

    cmd = f"##Command:\nWrite a single line of dialogue for {name} to fit the situation and {name}'s personality."

    return SYSTEM_PROMPT, GAME_CONTEXT + npc_ctx + core + inst + cmd

def send_request(system, user_prompt):
    body = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "thinking": {"type": "disabled"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt}
        ]
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        URL, data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    )

    start = time.time()
    resp = urllib.request.urlopen(req, timeout=60)
    elapsed = time.time() - start

    result = json.loads(resp.read().decode("utf-8"))
    msg = result["choices"][0]["message"]
    content = msg.get("content", "").strip()
    usage = result.get("usage", {})
    finish = result["choices"][0].get("finish_reason", "")

    return {
        "content": content,
        "elapsed": round(elapsed, 2),
        "tokens_in": usage.get("prompt_tokens", 0),
        "tokens_out": usage.get("completion_tokens", 0),
        "truncated": finish == "length"
    }

def build_conversation_prompt(name, info, scenario, history, chinese=False):
    system, base = build_prompt(name, info, scenario, chinese)

    conv = "##Current Conversation:\n"
    conv += f"The farmer and {name} are in the middle of a conversation.\n"
    for h in history:
        if h["role"] == "npc":
            conv += f"- {name}: {h['text']}\n"
        else:
            conv += f"- Farmer: {h['text']}\n"

    conv += "\n##Command:\n"
    conv += f"Write the next single line of dialogue for {name} to continue the conversation."

    return system, base + "\n" + conv

# ========== 3. 交互界面 ==========

def select_scenario(name, info, chinese):
    tag = " (中文)" if chinese else ""
    print(f"\n{'='*60}")
    print(f"  {name}{tag} - 配置场景")
    print(f"{'='*60}")

    seasons = ["spring", "summer", "fall", "winter"]
    print("\n选择季节:")
    for i, s in enumerate(seasons, 1):
        print(f"  {i}. {s.capitalize()}")
    season = seasons[int(input(f"  (1-4, 默认2): ") or "2") - 1]

    weathers = ["sunny", "rainy", "snowy", "stormy"]
    print("\n选择天气:")
    for i, w in enumerate(weathers, 1):
        print(f"  {i}. {w.capitalize()}")
    weather = weathers[int(input(f"  (1-4, 默认1): ") or "1") - 1]

    times = ["early morning", "late morning", "midday", "afternoon", "evening"]
    print("\n选择时间:")
    for i, t in enumerate(times, 1):
        print(f"  {i}. {t.capitalize()}")
    time_desc = times[int(input(f"  (1-5, 默认3): ") or "3") - 1]

    locations = [
        f"{name}'s home",
        "Pelican Town",
        "the beach",
        "the Saloon",
        "the mountains",
        "the farm",
        "Pierre's General Store",
        "the forest"
    ]
    print("\n选择地点:")
    for i, loc in enumerate(locations, 1):
        print(f"  {i}. {loc}")
    loc = locations[int(input(f"  (1-8, 默认1): ") or "1") - 1]
    location_desc = f"The farmer and {name} are talking at {loc}."

    friends = ["first meeting (very shy)", "strangers", "acquaintances",
               "friends", "close friends", "dating", "married"]
    print("\n选择关系程度:")
    for i, f in enumerate(friends, 1):
        print(f"  {i}. {f}")
    f_idx = int(input(f"  (1-7, 默认4): ") or "4") - 1
    friendship_descs = [
        f"This is the first time {name} has spoken to the farmer. {name} is very shy.",
        f"{name} and the farmer are strangers, though they have spoken before. {name} is not yet sure about the farmer.",
        f"{name} and the farmer are acquaintances, getting to know each other.",
        f"{name} and the farmer are friends. They know each other well.",
        f"{name} and the farmer are close friends. They share personal details and gossip.",
        f"{name} and the farmer are dating. There is growing romantic interest.",
        f"The farmer is married to {name} and they live together on the farm."
    ]
    friendship_desc = friendship_descs[f_idx]

    preocc = ""
    if info.get("preoccupations"):
        preocc = random.choice(info["preoccupations"])

    gender_input = input(f"\nFarmer gender (male/female, 默认 female): ") or "female"

    return {
        "season": season,
        "weather": weather,
        "time_desc": time_desc,
        "location_desc": location_desc,
        "friendship_desc": friendship_desc,
        "preoccupation": preocc,
        "farmer_gender": gender_input
    }

def show_dialogue(result):
    status = " [截断!]" if result.get("truncated") else ""
    print(f"\n  [{result['elapsed']}s | {result['tokens_in']}in + {result['tokens_out']}out]{status}")
    print(f"{'─'*50}")
    for line in result["content"].split("\n"):
        print(f"  {line}")
    print(f"{'─'*50}")

def chat_loop(name, info, scenario, chinese=False):
    history = []

    system, prompt = build_prompt(name, info, scenario, chinese)
    print(f"\n>>> 生成第一句对话...")
    r = send_request(system, prompt)
    show_dialogue(r)
    history.append({"role": "npc", "text": r["content"]})

    while True:
        print(f"\n{'·'*40}")
        reply = input("你的回应 (或输入 q 退出, n 新场景): ").strip()
        if reply.lower() == "q":
            break
        if reply.lower() == "n":
            return True

        history.append({"role": "player", "text": reply})
        system, prompt = build_conversation_prompt(name, info, scenario, history, chinese)
        print(f">>> {name} 思考中...")
        r = send_request(system, prompt)
        show_dialogue(r)
        history.append({"role": "npc", "text": r["content"]})

    return False


# ========== 主程序 ==========

print(f"\n{'#'*60}")
print(f"  ValleyTalk 对话模拟器")
print(f"  模型: {MODEL} | 加载了 {len(bios)} 个角色")
print(f"{'#'*60}")

lang = input(f"\n语言 Language (cn/en, 默认 cn): ").strip().lower() or "cn"
chinese = lang == "cn"

while True:
    names = sorted(bios.keys())
    cols = 4
    print(f"\n{'='*60}")
    print(f"  角色列表 ({'中文模式' if chinese else 'English mode'})")
    print(f"{'='*60}")
    for i, name in enumerate(names, 1):
        print(f"  {i:2d}. {name:<15}", end="\n" if i % cols == 0 else "")
    if len(names) % cols != 0:
        print()

    choice = input(f"\n选择角色 (1-{len(names)}, 或 q 退出): ").strip()
    if choice.lower() == "q":
        break

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(names):
            print("无效选择!")
            continue
        name = names[idx]
    except ValueError:
        print("请输入数字!")
        continue

    info = bios[name]
    scenario = select_scenario(name, info, chinese)
    new_scene = chat_loop(name, info, scenario, chinese)
    if not new_scene:
        break

print("\n再见!")

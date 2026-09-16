#!/usr/bin/env python3
"""Fetch a small, relevant batch of retro-flavoured GitHub repositories."""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "repositories.json"
API_ROOT = "https://api.github.com"
BATCH_SIZE = 10

SEARCH_QUERIES = (
    "topic:retro",
    "topic:retrogaming",
    "topic:pixel-art game",
    "emulator retro in:name,description",
    '"old school" game in:name,description',
)

# These make the first run useful even when GitHub search ranking is noisy.
# Search results can still displace them when a better, newer match appears.
CURATED_REPOSITORIES = (
    "OpenRCT2/OpenRCT2",
    "OpenTTD/OpenTTD",
    "OpenXcom/OpenXcom",
    "chocolate-doom/chocolate-doom",
    "EasyRPG/Player",
    "scummvm/scummvm",
    "dosbox-staging/dosbox-staging",
    "copy/v86",
    "Orama-Interactive/Pixelorama",
    "Swordfish90/cool-retro-term",
    "LibreSprite/LibreSprite",
    "mapeditor/tiled",
    "86Box/86Box",
    "libretro/RetroArch",
    "nxengine/nxengine-evo",
    "OpenMW/openmw",
)

EDITORIAL = {
    "OpenRCT2/OpenRCT2": {"category": "游戏", "tags": ["模拟经营", "多人", "开放世界"], "note": "把主题公园经营搬回 CRT 屏幕：过山车、像素游客和一整套不肯退休的模拟经营系统。", "visual": "rct"},
    "OpenTTD/OpenTTD": {"category": "游戏", "tags": ["运输模拟", "等距视角", "沙盒"], "note": "铁路、公路、港口和那种一开局就停不下来的运输帝国。复古等距视角依旧很有魔力。", "visual": "transport"},
    "OpenXcom/OpenXcom": {"category": "游戏", "tags": ["回合制", "战术", "X-COM"], "note": "把外星人入侵、回合制战术和基地管理重新装进一台 486。紧张感没有随着分辨率一起消失。", "visual": "xcom"},
    "chocolate-doom/chocolate-doom": {"category": "游戏", "tags": ["FPS", "历史准确", "SDL2"], "note": "不加滤镜、不追求花哨，只让经典 FPS 按照记忆里的速度和噪声再次启动。", "visual": "doom"},
    "EasyRPG/Player": {"category": "游戏", "tags": ["RPG Maker", "剧情游戏", "跨平台"], "note": "让 RPG Maker 2000/2003 时代的地图、对白和存档，在今天的设备上继续旅行。", "visual": "rpg"},
    "scummvm/scummvm": {"category": "模拟器", "tags": ["冒险游戏", "引擎合集", "多平台"], "note": "一只很聪明的时间机器：让经典图形冒险游戏在现代系统里保留原本的气质。", "visual": "scumm"},
    "dosbox-staging/dosbox-staging": {"category": "模拟器", "tags": ["MS-DOS", "兼容性", "复古计算"], "note": "给 MS-DOS 游戏准备的一间现代化放映室：兼容性更好，但仍然保留那行闪烁的命令提示符。", "visual": "dos"},
    "copy/v86": {"category": "模拟器", "tags": ["浏览器", "x86", "WebAssembly"], "note": "直接在浏览器里启动一台 x86 电脑。像把整台旧 PC 折成一张网页，再塞进书签。", "visual": "pc"},
    "Orama-Interactive/Pixelorama": {"category": "编辑器", "tags": ["像素绘画", "精灵动画", "Godot"], "note": "像素画、精灵、瓦片和动画，一把把旧游戏的视觉零件重新拼起来。", "visual": "sprite"},
    "LibreSprite/LibreSprite": {"category": "编辑器", "tags": ["Sprite", "动画", "GPLv2"], "note": "一款坚持像素边缘的精灵编辑器，适合给下一款小小的 2D 游戏准备主角。", "visual": "sprite"},
    "mapeditor/tiled": {"category": "编辑器", "tags": ["地图编辑", "瓦片", "关卡设计"], "note": "把地图、碰撞和关卡逻辑铺在一张熟悉的瓦片纸上，适合认真做一款 2D 游戏。", "visual": "transport"},
    "Swordfish90/cool-retro-term": {"category": "工具", "tags": ["CRT", "终端", "复古计算"], "note": "把终端变成一台会发光的老电视：扫描线、磷光和 CRT 噪点都可以调到你喜欢的程度。", "visual": "terminal"},
    "86Box/86Box": {"category": "模拟器", "tags": ["x86", "PC 模拟", "硬件考古"], "note": "精确模拟旧 x86 机器，把 BIOS 哔声、软盘和显卡兼容性一起保存下来。", "visual": "pc"},
    "libretro/RetroArch": {"category": "模拟器", "tags": ["多平台", "模拟核心", "手柄"], "note": "一套把不同主机模拟核心收进同一个前端的复古游戏工作台。", "visual": "pc"},
    "nxengine/nxengine-evo": {"category": "游戏", "tags": ["2D", "引擎", "复古动作"], "note": "为经典 2D 动作冒险体验准备的现代化引擎重构。", "visual": "rpg"},
    "OpenMW/openmw": {"category": "游戏", "tags": ["RPG", "开放世界", "引擎重制"], "note": "让一块经典 RPG 开放世界在现代硬件上继续生长，保留探索感与手工地图的尺度。", "visual": "rpg"},
}

POSITIVE_TERMS = (
    "retro", "retrogam", "pixel", "8-bit", "8bit", "16-bit", "16bit", "dos", "ms-dos",
    "emulat", "arcade", "classic", "vintage", "old school", "old-school", "crt", "terminal",
    "rpg maker", "sprite", "scumm", "doom", "tycoon", "x86", "wasm",
)
REJECT_TERMS = ("awesome list", "list of", "tutorial", "course", "roadmap", "interview", "collection of resources")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def request_json(path: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RetroWhisper-bot/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{API_ROOT}{path}", headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_repo(full_name: str) -> dict | None:
    try:
        return request_json(f"/repos/{full_name}")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"[warn] unable to fetch {full_name}: {error}", file=sys.stderr)
        return None


def search_repositories(query: str) -> list[dict]:
    params = urlencode({"q": f"{query} is:public archived:false", "sort": "stars", "order": "desc", "per_page": 30})
    try:
        return request_json(f"/search/repositories?{params}").get("items", [])
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"[warn] search failed for {query!r}: {error}", file=sys.stderr)
        return []


def searchable_text(repo: dict) -> str:
    topics = " ".join(repo.get("topics") or [])
    return " ".join((repo.get("name") or "", repo.get("description") or "", topics)).lower()


def classify(repo: dict) -> str:
    name = repo.get("full_name", "")
    if name in EDITORIAL:
        return EDITORIAL[name]["category"]
    text = searchable_text(repo)
    if any(term in text for term in ("pixel-art", "pixel art", "sprite", "tile editor", "level editor")):
        return "编辑器"
    if any(term in text for term in ("emulator", "emulation", "dosbox", "retroarch", "scummvm")):
        return "模拟器"
    if any(term in text for term in ("game", "rpg", "arcade", "doom", "adventure", "tycoon")):
        return "游戏"
    return "工具"


def score(repo: dict) -> float:
    full_name = repo.get("full_name", "")
    text = searchable_text(repo)
    if any(term in text for term in REJECT_TERMS) or repo.get("name", "").lower().startswith("awesome"):
        return -1000
    positive_hits = sum(1 for term in POSITIVE_TERMS if term in text)
    topic_hits = sum(1 for term in POSITIVE_TERMS if term in " ".join(repo.get("topics") or []).lower())
    stars = max(0, int(repo.get("stargazers_count") or 0))
    curated_bonus = 32 if full_name in EDITORIAL else 0
    return math.log10(stars + 1) * 9 + positive_hits * 4 + topic_hits * 5 + curated_bonus


def normalise(repo: dict, index: int) -> dict:
    full_name = repo.get("full_name") or repo.get("name") or "unknown/relic"
    editorial = EDITORIAL.get(full_name, {})
    license_info = repo.get("license") or {}
    return {
        "id": full_name,
        "full_name": full_name,
        "owner": (repo.get("owner") or {}).get("login") or full_name.split("/")[0],
        "name": repo.get("name") or full_name.split("/")[-1],
        "html_url": repo.get("html_url") or f"https://github.com/{full_name}",
        "cover": f"https://opengraph.githubassets.com/1/{full_name}",
        "description": repo.get("description") or "一个值得被重新发现的开源项目。",
        "editor_note": editorial.get("note") or "一个值得被重新发现的复古开源项目。",
        "stars": int(repo.get("stargazers_count") or 0),
        "language": repo.get("language") or "多语言",
        "license": license_info.get("spdx_id") or "NOASSERTION",
        "updated_at": repo.get("updated_at") or repo.get("pushed_at") or now_iso(),
        "category": editorial.get("category") or classify(repo),
        "tags": editorial.get("tags") or [topic.replace("-", " ") for topic in (repo.get("topics") or [])[:3]],
        "topics": repo.get("topics") or [],
        "visual": editorial.get("visual") or "default",
        "curated_index": index,
    }


def select_repositories(candidates: dict[str, dict]) -> list[dict]:
    viable = [repo for repo in candidates.values() if score(repo) > -100]
    ranked = sorted(viable, key=score, reverse=True)
    selected: list[dict] = []
    # Keep the feed visually and thematically mixed instead of returning ten emulators.
    for category in ("游戏", "模拟器", "编辑器", "工具"):
        match = next((repo for repo in ranked if classify(repo) == category), None)
        if match and match not in selected:
            selected.append(match)
    for repo in ranked:
        if repo not in selected:
            selected.append(repo)
        if len(selected) == BATCH_SIZE:
            break
    return [normalise(repo, index) for index, repo in enumerate(selected[:BATCH_SIZE])]


def load_existing() -> dict:
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"items": []}


def main() -> int:
    candidates: dict[str, dict] = {}
    for full_name in CURATED_REPOSITORIES:
        repo = fetch_repo(full_name)
        if repo and not repo.get("archived"):
            candidates[repo["full_name"]] = repo
    for query in SEARCH_QUERIES:
        for repo in search_repositories(query):
            if repo.get("full_name") and not repo.get("archived"):
                candidates[repo["full_name"]] = repo

    items = select_repositories(candidates)
    if len(items) < BATCH_SIZE:
        existing_items = load_existing().get("items", [])
        selected_names = {entry.get("full_name") for entry in items}
        for item in existing_items:
            if item.get("full_name") not in selected_names:
                items.append(item)
                selected_names.add(item.get("full_name"))
            if len(items) == BATCH_SIZE:
                break
    if not items:
        print("[error] no repositories were fetched and no previous data exists", file=sys.stderr)
        return 1

    payload = {
        "updated_at": now_iso(),
        "source": "GitHub Search API",
        "refresh_hours": 6,
        "items": items[:BATCH_SIZE],
    }
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] wrote {len(payload['items'])} recommendations to {DATA_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

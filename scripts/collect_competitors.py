#!/usr/bin/env python3
"""采集 AI Website Builder 竞品信息，输出 competitors.json。"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from monitor import run_competitor_monitor

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "data" / "competitors_config.json"
OUTPUT_PATH = BASE_DIR / "data" / "competitors.json"

REQUEST_TIMEOUT = 20
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

PRICING_PATTERN = re.compile(
    r"(?:\$|€|£)\s?\d+(?:[.,]\d{2})?(?:\s*/\s*(?:mo|month|yr|year))?"
    r"|(?:free|starter|pro|team|enterprise|business)\s*(?:plan)?",
    re.IGNORECASE,
)
FEATURE_KEYWORDS = (
    "feature",
    "build",
    "deploy",
    "ai",
    "code",
    "design",
    "template",
    "integrat",
    "collabor",
    "host",
    "export",
    "seo",
    "crm",
    "website",
    "marketing",
    "booking",
    "database",
    "publish",
    "prototype",
)

MAX_FEATURE_LEN = 80

NON_FEATURE_EXACT = frozenset({
    "resources",
    "community",
    "blog",
    "docs",
    "documentation",
    "press",
    "media",
    "trust center",
    "linkedin",
    "twitter",
    "twitter/x",
    "x",
    "instagram",
    "facebook",
    "youtube",
    "tiktok",
    "partnerships",
    "careers",
    "about",
    "contact",
    "press & media",
    "press and media",
    "solutions",
    "enterprise",
    "products",
    "security",
    "ambassadors",
    "students",
    "student discount",
    "ai policy",
    "vercel community",
    "what are you waiting for?",
})

# Persona / audience segment labels (not product capabilities)
PERSONA_LABELS = frozenset({
    "founders",
    "founder",
    "designers",
    "designer",
    "marketers",
    "marketer",
    "product managers",
    "product manager",
    "students",
    "student",
    "developers",
    "developer",
    "agencies",
    "agency",
    "teams",
    "team",
})

# UI control labels and marketing segments mistaken as features
NOISE_LABELS = frozenset({
    "speed high",
    "intelligence high",
    "token cost balanced",
    "connections",
    "internal tools",
    "ready to build?",
    "build something lovable",
})

LEGAL_FOOTER_FRAGMENTS = (
    "do not sell",
    "personal information",
    "code of conduct",
    "privacy policy",
    "cookie policy",
    "registration terms",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(path: Path) -> list[dict[str, Any]]:
    """从配置文件读取竞品列表。"""
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    competitors = data.get("competitors")
    if not isinstance(competitors, list) or not competitors:
        raise ValueError("competitors_config.json 中缺少有效的 competitors 数组")

    return competitors


def fetch_html(url: str, session: requests.Session) -> str | None:
    """请求页面 HTML，失败时返回 None。"""
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logger.warning("请求失败 %s: %s", url, exc)
        return None


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_valid_core_feature(text: str) -> bool:
    """过滤导航项、Persona、社媒链接与过长营销文案。"""
    cleaned = clean_text(text)
    if len(cleaned) < 8 or len(cleaned) > MAX_FEATURE_LEN:
        return False

    lower = re.sub(r"\s+", " ", cleaned.lower()).strip()
    if lower in NON_FEATURE_EXACT:
        return False

    if lower in PERSONA_LABELS or lower in NOISE_LABELS:
        return False

    if any(frag in lower for frag in LEGAL_FOOTER_FRAGMENTS):
        return False

    if lower in ("twitter/x", "x / twitter"):
        return False

    words = lower.split()
    if words and words[0] in NON_FEATURE_EXACT and len(words) >= 4:
        return False

    # 短标签：整句主要由导航词组成则丢弃
    if len(cleaned) <= 35:
        for noise in NON_FEATURE_EXACT:
            if noise == "x" and lower != "x":
                continue
            if lower == noise or lower.startswith(f"{noise} ") or lower.endswith(f" {noise}"):
                return False
            if f" {noise} " in f" {lower} " and len(cleaned) <= 25:
                return False

    # 短文本须包含产品能力关键词，否则多为 Persona / 导航 / 营销标签
    if len(cleaned) <= 40 and not any(kw in lower for kw in FEATURE_KEYWORDS):
        return False

    return True


def filter_core_features(items: list[str]) -> list[str]:
    return [item for item in items if is_valid_core_feature(item)]


def extract_meta_description(soup: BeautifulSoup) -> str:
    tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if tag and tag.get("content"):
        return clean_text(tag["content"])
    og = soup.find("meta", property="og:description")
    if og and og.get("content"):
        return clean_text(og["content"])
    return ""


def extract_list_items(soup: BeautifulSoup, limit: int = 8) -> list[str]:
    items: list[str] = []
    for li in soup.find_all("li"):
        text = clean_text(li.get_text(" ", strip=True))
        if not is_valid_core_feature(text):
            continue
        if text.lower() in {i.lower() for i in items}:
            continue
        items.append(text)
        if len(items) >= limit:
            break
    return items


def extract_headings_as_features(soup: BeautifulSoup, limit: int = 6) -> list[str]:
    features: list[str] = []
    for tag in soup.find_all(["h2", "h3", "h4"]):
        text = clean_text(tag.get_text(" ", strip=True))
        if not is_valid_core_feature(text):
            continue
        lower = text.lower()
        if any(kw in lower for kw in FEATURE_KEYWORDS):
            features.append(text)
        if len(features) >= limit:
            break
    return features


def extract_pricing_text(soup: BeautifulSoup) -> str:
    candidates: list[str] = []

    for node in soup.find_all(string=PRICING_PATTERN):
        parent_text = clean_text(node.parent.get_text(" ", strip=True) if node.parent else str(node))
        if 3 < len(parent_text) < 180:
            candidates.append(parent_text)

    for tag in soup.find_all(["span", "p", "div", "h2", "h3"], limit=300):
        text = clean_text(tag.get_text(" ", strip=True))
        if PRICING_PATTERN.search(text) and 3 < len(text) < 180:
            candidates.append(text)

    if not candidates:
        return ""

    unique: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return " | ".join(unique[:5])


def extract_technical_highlights(soup: BeautifulSoup, description: str) -> list[str]:
    highlights: list[str] = []
    tech_keywords = (
        "react",
        "next.js",
        "nextjs",
        "typescript",
        "tailwind",
        "supabase",
        "vercel",
        "github",
        "api",
        "full-stack",
        "full stack",
        "open source",
        "cloud",
        "database",
        "deploy",
    )

    combined = f"{description} ".lower()
    for tag in soup.find_all(["p", "li", "span"], limit=200):
        combined += clean_text(tag.get_text(" ", strip=True)).lower() + " "

    for kw in tech_keywords:
        if kw in combined:
            label = kw.replace("nextjs", "Next.js").title() if kw != "next.js" else "Next.js"
            if label not in highlights:
                highlights.append(label)

    return highlights[:6]


def merge_unique(primary: list[str], secondary: list[str], limit: int = 8) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in primary + secondary:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            merged.append(item)
        if len(merged) >= limit:
            break
    return merged


def empty_record(name: str, website: str) -> dict[str, Any]:
    return {
        "name": name,
        "website": website,
        "pricing": "",
        "target_customer": "",
        "core_features": [],
        "technical_highlights": [],
    }


def apply_overrides(record: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """允许配置中为单个竞品提供静态补充字段。"""
    if not overrides:
        return record

    for key in ("pricing", "target_customer", "website"):
        if overrides.get(key):
            record[key] = overrides[key]

    for key in ("core_features", "technical_highlights"):
        if overrides.get(key):
            record[key] = merge_unique(record.get(key, []), list(overrides[key]))

    return record


def collect_one(entry: dict[str, Any], session: requests.Session) -> dict[str, Any]:
    """采集单个竞品，失败时返回空字段记录。"""
    name = entry.get("name", "").strip()
    website = entry.get("website", "").strip()
    if not name or not website:
        raise ValueError("竞品配置缺少 name 或 website")

    record = empty_record(name, website)
    overrides = entry.get("overrides") or {}

    pages: list[str] = []
    homepage_html = fetch_html(website, session)
    if homepage_html:
        pages.append(homepage_html)

    pricing_url = entry.get("pricing_url") or urljoin(website.rstrip("/") + "/", "pricing")
    if pricing_url != website:
        pricing_html = fetch_html(pricing_url, session)
        if pricing_html:
            pages.append(pricing_html)

    if not pages:
        logger.warning("[%s] 无法获取任何页面，使用 overrides（如有）", name)
        return apply_overrides(record, overrides)

    home_soup = BeautifulSoup(pages[0], "html.parser")
    description = extract_meta_description(home_soup)
    record["target_customer"] = description

    list_features = extract_list_items(home_soup)
    heading_features = extract_headings_as_features(home_soup)
    record["core_features"] = merge_unique(
        filter_core_features(list_features),
        filter_core_features(heading_features),
    )

    pricing_parts: list[str] = []
    for html in pages:
        soup = BeautifulSoup(html, "html.parser")
        part = extract_pricing_text(soup)
        if part:
            pricing_parts.append(part)

    if pricing_parts:
        record["pricing"] = " | ".join(dict.fromkeys(pricing_parts))

    all_soup = BeautifulSoup("\n".join(pages), "html.parser")
    record["technical_highlights"] = extract_technical_highlights(all_soup, description)

    return apply_overrides(record, overrides)


def collect_all(config_path: Path = CONFIG_PATH, output_path: Path = OUTPUT_PATH) -> list[dict[str, Any]]:
    """采集全部竞品并写入 JSON。"""
    competitors_config = load_config(config_path)
    results: list[dict[str, Any]] = []

    with requests.Session() as session:
        session.headers.update(HEADERS)

        for entry in competitors_config:
            name = entry.get("name", "Unknown")
            try:
                logger.info("正在采集: %s", name)
                record = collect_one(entry, session)
                results.append(record)
                logger.info("[%s] 采集完成", name)
            except Exception as exc:
                logger.error("[%s] 采集失败: %s", name, exc, exc_info=True)
                fallback = empty_record(name, entry.get("website", ""))
                results.append(apply_overrides(fallback, entry.get("overrides") or {}))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info("已写入 %d 条记录 -> %s", len(results), output_path)
    run_competitor_monitor(results)
    return results


def main() -> int:
    try:
        collect_all()
        return 0
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.error("配置错误: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

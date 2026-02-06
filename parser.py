# parser.py
import asyncio
import json
import logging
import random
import re
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; K) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}


async def _download_page(url: str, timeout: int = 15) -> str:
    """Async fetch with up‑to‑3 retries."""
    async with httpx.AsyncClient(headers=HEADERS, timeout=timeout) as client:
        for attempt in range(1, 4):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.text
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                logger.warning(f"Attempt {attempt} – error fetching {url}: {exc}")
                if attempt == 3:
                    raise
                await asyncio.sleep(2**attempt)


def _extract_from_json(data: dict) -> List[Dict]:
    found = []

    def walk(obj):
        if isinstance(obj, dict):
            if "id" in obj and isinstance(obj.get("images"), dict):
                if obj.get("is_promoted"):
                    return
                images = obj["images"]
                for key in ("orig", "1200x", "736x", "474x"):
                    if key in images:
                        found.append(
                            {
                                "id": obj["id"],
                                "url": images[key]["url"],
                                "description": obj.get("description", ""),
                                "is_promoted": False,
                            }
                        )
                        break
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)

    walk(data)
    return found


def _extract_from_html(soup: BeautifulSoup) -> List[Dict]:
    items = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or "pinimg.com" not in src:
            continue
        if any(x in src for x in ("30x30", "75x75", "20x20")):
            continue
        high_res = src
        if "/236x/" in src:
            high_res = src.replace("/236x/", "/736x/")
        elif "/474x/" in src:
            high_res = src.replace("/474x/", "/736x/")
        try:
            pseudo_id = src.split("/")[-1].split(".")[0]
        except Exception:
            pseudo_id = f"pseudo_{random.randint(1_000_000, 9_999_999)}"
        items.append(
            {
                "id": pseudo_id,
                "url": high_res,
                "description": img.get("alt", ""),
                "is_promoted": False,
            }
        )
    return items


async def get_pinterest_images(url: str) -> List[Dict]:
    """
    Возвращает список пинов из переданного URL.
    """
    try:
        html = await _download_page(url)
    except Exception as exc:
        logger.error(f"Failed to download Pinterest page: {exc}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []

    # JSON‑скрипты
    json_scripts = soup.find_all(
        "script", id=re.compile(r"__PWS_(DATA|INITIAL_PROPS)__")
    )
    for script in json_scripts:
        try:
            data = json.loads(script.string or "{}")
            results.extend(_extract_from_json(data))
        except Exception as exc:
            logger.debug(
                f"JSON parsing error in script {script.get('id')}: {exc}"
            )

    # Если JSON ничего не смог выдать – HTML
    if not results:
        logger.info("JSON gave no pins → fallback to <img>")
        results.extend(_extract_from_html(soup))

    # Убираем дубли
    uniq = {}
    for item in results:
        key = item.get("id") or item.get("url")
        if key and key not in uniq:
            uniq[key] = item

    logger.info(f"Found {len(uniq)} unique pins")
    return list(uniq.values())

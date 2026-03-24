from __future__ import annotations

import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from html import unescape

from models import PublicMemoryState


def fetch_url_text(url: str, max_chars: int = 12000, *, project_name: str, version: str) -> dict:
    req = urllib.request.Request(str(url), headers={"User-Agent": f"{project_name}/{version}"})
    insecure_ssl_fallback_used = False
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read(1024 * 1024)
            content_type = str(resp.headers.get("Content-Type", ""))
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        insecure_ssl_fallback_used = True
        insecure_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=20, context=insecure_context) as resp:
            raw = resp.read(1024 * 1024)
            content_type = str(resp.headers.get("Content-Type", ""))
    html_text = raw.decode("utf-8", errors="replace")
    text = html_text
    title = ""
    if "html" in content_type.lower() or "<html" in text.lower():
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.I | re.S)
        if title_match:
            title = unescape(re.sub(r"\s+", " ", title_match.group(1))).strip()
        body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, flags=re.I | re.S)
        body_html = body_match.group(1) if body_match else html_text
        candidate_blocks = []
        for pattern in [
            r"<(article|main)[^>]*>(.*?)</\1>",
            r"<(section|div)[^>]+class=[\"'][^\"']*(content|article|post|entry|main|body|story|markdown)[^\"']*[\"'][^>]*>(.*?)</\1>",
        ]:
            for match in re.finditer(pattern, body_html, flags=re.I | re.S):
                block = match.group(match.lastindex or 1)
                candidate_blocks.append(block)
        working_html = max(candidate_blocks, key=len) if candidate_blocks else body_html
        for pattern in [r"<script.*?</script>", r"<style.*?</style>", r"<noscript.*?</noscript>", r"<svg.*?</svg>", r"<nav.*?</nav>", r"<footer.*?</footer>", r"<header.*?</header>", r"<aside.*?</aside>", r"<form.*?</form>", r"<button.*?</button>"]:
            working_html = re.sub(pattern, " ", working_html, flags=re.I | re.S)
        block_parts = re.split(r"</?(p|li|h1|h2|h3|blockquote|section|article|main|div)[^>]*>", working_html, flags=re.I)
        readability_chunks = []
        for part in block_parts:
            plain = unescape(re.sub(r"<[^>]+>", " ", part))
            plain = re.sub(r"\s+", " ", plain).strip()
            if len(plain) < 60:
                continue
            if plain.count(" ") < 8:
                continue
            lowered = plain.lower()
            if any(noise in lowered for noise in ["cookie policy", "privacy policy", "all rights reserved", "sign in", "subscribe", "follow us", "shop now", "advertisement", "skip to main content", "my account", "contact us login", "journals & books help", "submit cancel"]):
                continue
            score = len(plain)
            score += plain.count('.') * 8 + plain.count('?') * 5
            if any(token in lowered for token in [" is ", " are ", " was ", " were ", " means ", " defined ", " refers to "]):
                score += 25
            readability_chunks.append((score, plain))
        readability_chunks.sort(key=lambda item: item[0], reverse=True)
        text = " ".join(chunk for _, chunk in readability_chunks[:12]) or unescape(re.sub(r"<[^>]+>", " ", working_html))
    text = unescape(text)
    text = re.sub(r"\b(login|sign in|subscribe|cookie policy|privacy policy|all rights reserved|shop now|follow us|menu|skip to main content|my account|search close|submit cancel|donate)\b", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    raw_excerpt = text[:max(500, int(max_chars))]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    cleaned_sentences = []
    seen = set()
    for sentence in sentences:
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if len(sentence) < 50:
            continue
        lowered = sentence.lower()
        if lowered in seen:
            continue
        if sentence.count("|") > 1 or sentence.count("·") > 2:
            continue
        if any(noise in lowered for noise in ["copyright", "all rights reserved", "follow follow", "shop now", "curriculum access", "contact us login", "submit cancel", "journals & books help", "layout insert", "position left position right"]):
            continue
        seen.add(lowered)
        cleaned_sentences.append(sentence)
    cleaned_text = " ".join(cleaned_sentences)[:max(500, int(max_chars))]
    return {
        "url": str(url),
        "title": title or str(url),
        "content_type": content_type,
        "text": cleaned_text,
        "raw_excerpt": raw_excerpt,
        "insecure_ssl_fallback_used": insecure_ssl_fallback_used,
        "fetched_at": int(time.time()),
    }


def search_web(query: str, limit: int = 5, *, project_name: str, version: str) -> dict:
    query = str(query or "").strip()
    if not query:
        return {"query": "", "results": []}
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": f"{project_name}/{version}"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read(1024 * 1024).decode("utf-8", errors="replace")
    matches = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.I | re.S)
    results = []
    for href, title_html in matches[:max(1, int(limit))]:
        title = unescape(re.sub(r"<[^>]+>", " ", title_html))
        title = re.sub(r"\s+", " ", title).strip()
        resolved_url = str(href)
        if "uddg=" in resolved_url:
            parsed = urllib.parse.urlparse(resolved_url)
            qs = urllib.parse.parse_qs(parsed.query)
            uddg = (qs.get("uddg") or [""])[0]
            if uddg:
                resolved_url = urllib.parse.unquote(uddg)
        elif resolved_url.startswith("//"):
            resolved_url = "https:" + resolved_url
        results.append({"title": title, "url": resolved_url})
    return {"query": query, "results": results, "fetched_at": int(time.time())}


def ingest_web_resource(url: str, title: str = "", max_chars: int = 12000, *, fetch_url_text_func, load_public_memory, save_public_memory) -> dict:
    fetched = fetch_url_text_func(url, max_chars=max_chars)
    public_memory = load_public_memory()
    now_ts = int(time.time())
    note_item = PublicMemoryState(
        id=f"web-note-{now_ts}",
        title=title or fetched.get("title") or str(url),
        kind="research",
        content=fetched.get("text", ""),
        source=str(url),
        stability=0.42,
        created_at=now_ts,
        updated_at=now_ts,
    ).to_dict()
    raw_item = PublicMemoryState(
        id=f"web-raw-{now_ts}",
        title=f"Raw excerpt: {title or fetched.get('title') or str(url)}",
        kind="research_raw",
        content=fetched.get("raw_excerpt", fetched.get("text", "")),
        source=str(url),
        stability=0.28,
        created_at=now_ts,
        updated_at=now_ts,
    ).to_dict()
    public_memory.extend([note_item, raw_item])
    save_public_memory(public_memory[-120:])
    return {"saved": [note_item, raw_item], "fetched": fetched, "public_memory_count": len(load_public_memory())}


def score_search_result(query: str, result: dict) -> float:
    query_terms = [part for part in re.split(r"\W+", str(query or "").lower()) if part and len(part) > 2]
    title = str(result.get("title") or "").lower()
    url = str(result.get("url") or "").lower()
    score = 0.0
    for term in query_terms[:8]:
        if term and term in title:
            score += 0.22
        if term and term in url:
            score += 0.06
    strong_domains = [
        "wikipedia.org", "stanford.edu", "mit.edu", "arxiv.org", "nature.com", "sciencedirect.com",
        "springer.com", "nih.gov", "ncbi.nlm.nih.gov", "knowablemagazine.org", "mozilla.org",
        "python.org", "github.com", "docs.", "developer."
    ]
    medium_domains = ["researchgate.net", ".edu", ".gov", ".org"]
    weak_domains = ["pinterest.", "facebook.", "instagram.", "tiktok.", "reddit.com/r/", "autismhelper.com", "silentinnovator.com", "bcbamockexam.com"]
    for domain in strong_domains:
        if domain in url:
            score += 0.55
            break
    else:
        for domain in medium_domains:
            if domain in url:
                score += 0.22
                break
    for domain in weak_domains:
        if domain in url:
            score -= 0.28
            break
    if any(word in title for word in ["overview", "encyclopedia", "guide", "review", "definition"]):
        score += 0.08
    if len(title) >= 18:
        score += 0.05
    return round(score, 4)


def summarize_research_findings(query: str, fetched_items: list[dict]) -> str:
    if not fetched_items:
        return f"No readable source was fetched yet for {query}."
    summary_points = []
    evidence_lines = []
    seen_sentences = set()
    for item in fetched_items[:2]:
        text = str(item.get("text") or "")
        title = str(item.get("title") or item.get("url") or "source")
        parts = re.split(r"(?<=[.!?])\s+", text)
        kept = []
        for part in parts:
            cleaned = re.sub(r"\s+", " ", part).strip()
            if len(cleaned) < 60:
                continue
            key = cleaned.lower()
            if key in seen_sentences:
                continue
            if any(noise in key for noise in ["login", "subscribe", "cookie", "shop now", "follow follow"]):
                continue
            seen_sentences.add(key)
            kept.append(cleaned)
            if len(kept) >= 2:
                break
        if kept:
            summary_points.append(kept[0])
            evidence_lines.append(f"{title}: {' '.join(kept[:2])}")
    summary_points = summary_points[:3]
    if not summary_points:
        return f"Readable sources were fetched for {query}, but no compact synthesis could be formed yet."
    distilled = " ".join(summary_points)
    return "\n".join([
        f"Working summary for {query}: {distilled[:900]}",
        "",
        "Evidence:",
        *evidence_lines[:2],
    ])[:2600]

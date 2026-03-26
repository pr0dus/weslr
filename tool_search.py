# tool_search.py - Search for tools/APIs, read docs, extract usage
from __future__ import annotations

import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html import unescape


def search_for_tool(need: str, limit: int = 5) -> dict:
    """Search the web for tools/APIs matching a need."""
    need = str(need or "").strip()
    if not need:
        return {
            "ok": False,
            "error": "No need specified. Example: 'python web page reader library'",
        }

    # Build search query
    query = f"python {need} library api"
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "CircleForge/v0.5"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read(1024 * 1024).decode("utf-8", errors="replace")
    except Exception as e:
        return {
            "ok": False,
            "error": f"Search failed: {e}",
        }

    # Extract results
    matches = re.findall(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        html,
        flags=re.I | re.S,
    )

    results = []
    for href, title_html in matches[:limit]:
        title = unescape(re.sub(r"<[^>]+>", " ", title_html))
        title = re.sub(r"\s+", " ", title).strip()
        resolved_url = str(href)
        if "uddg=" in resolved_url:
            parsed = urllib.parse.urlparse(resolved_url)
            qs = urllib.parse.parse_qs(parsed.query)
            uddg = (qs.get("uddg") or [""])[0]
            if uddg:
                resolved_url = urllib.parse.unquote(uddg)

        results.append({
            "title": title,
            "url": resolved_url,
        })

    return {
        "ok": True,
        "query": query,
        "results": results,
        "generated_at": int(time.time()),
    }


def fetch_url_text(url: str, max_chars: int = 8000) -> dict:
    """Fetch readable text from a URL."""
    url = str(url).strip()
    if not url:
        return {"ok": False, "error": "No URL provided."}

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CircleForge/v0.5"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(1024 * 1024)
            content_type = str(resp.headers.get("Content-Type", ""))
    except Exception as e:
        return {"ok": False, "error": f"Fetch failed: {e}"}

    html_text = raw.decode("utf-8", errors="replace")
    text = html_text
    title = ""

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.I | re.S)
    if title_match:
        title = unescape(re.sub(r"\s+", " ", title_match.group(1))).strip()

    # Try to extract body content
    if "html" in content_type.lower() or "<html" in html_text.lower():
        body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, flags=re.I | re.S)
        body_html = body_match.group(1) if body_match else html_text

        # Remove common noise elements
        for pattern in [
            r"<script.*?</script>",
            r"<style.*?</style>",
            r"<nav.*?</nav>",
            r"<footer.*?</footer>",
            r"<header.*?</header>",
        ]:
            body_html = re.sub(pattern, " ", body_html, flags=re.I | re.S)

        # Extract paragraphs
        blocks = re.split(r"</?(p|li|h1|h2|h3|blockquote)[^>]*>", body_html, flags=re.I)
        chunks = []
        for block in blocks:
            plain = unescape(re.sub(r"<[^>]+>", " ", block))
            plain = re.sub(r"\s+", " ", plain).strip()
            if len(plain) < 60:
                continue
            if plain.count(" ") < 8:
                continue
            chunks.append(plain)
            if len(chunks) >= 8:
                break

        text = " ".join(chunks) if chunks else unescape(re.sub(r"<[^>]+>", " ", body_html))

    text = unescape(text)
    text = re.sub(r"\b(login|sign in|subscribe|cookie policy|privacy policy|shop now|follow us)\b", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    text = text[:max_chars]

    return {
        "ok": True,
        "url": url,
        "title": title or url,
        "text": text,
        "length": len(text),
        "fetched_at": int(time.time()),
    }


def extract_api_usage(text: str) -> list[dict]:
    """Extract API usage examples from text."""
    text = str(text or "")

    # Look for code blocks (Python examples)
    code_blocks = re.findall(r"```(?:python)?(.*?)```", text, flags=re.S)
    inline_code = re.findall(r"`([^`]+)`", text)

    examples = []

    # Process code blocks
    for block in code_blocks[:3]:
        block = block.strip()
        if not block:
            continue
        # Extract function calls
        functions = re.findall(r"(\w+)\s*\(", block)
        imports = re.findall(r"import\s+(\w+)", block)
        examples.append({
            "type": "code_block",
            "content": block[:500],
            "functions": functions[:5],
            "imports": imports[:3],
        })

    # Process inline code snippets
    for snippet in inline_code[:3]:
        snippet = snippet.strip()
        if not snippet or len(snippet) < 5:
            continue
        functions = re.findall(r"(\w+)\s*\(", snippet)
        imports = re.findall(r"import\s+(\w+)", snippet)
        examples.append({
            "type": "inline",
            "content": snippet[:100],
            "functions": functions[:3],
            "imports": imports[:2],
        })

    return examples


def synthesize_usage(tool_name: str, examples: list[dict]) -> dict:
    """Synthesize a usage pattern from examples."""
    if not examples:
        return {
            "ok": False,
            "error": "No usage examples found.",
        }

    # Extract common patterns
    functions = []
    imports = []
    for ex in examples:
        functions.extend(ex.get("functions", []))
        imports.extend(ex.get("imports", []))

    # Dedupe
    functions = list(dict.fromkeys(functions))[:6]
    imports = list(dict.fromkeys(imports))[:4]

    # Build pattern
    pattern_parts = []
    if imports:
        pattern_parts.append(f"# Import {', '.join(imports)}")
        pattern_parts.append("import " + ", ".join(imports))

    pattern_parts.append(f"# Use {tool_name}")
    if functions:
        pattern_parts.append(f"# Example: {functions[0]}(...)")

    return {
        "ok": True,
        "tool_name": tool_name,
        "imports": imports,
        "functions": functions,
        "pattern": "\n".join(pattern_parts),
        "examples_count": len(examples),
    }


def search_tool_and_synthesize(need: str) -> dict:
    """Full workflow: search for tool → fetch docs → extract usage → synthesize."""
    # Step 1: search
    search_result = search_for_tool(need, limit=3)
    if not search_result.get("ok"):
        return search_result

    results = search_result.get("results", [])
    if not results:
        return {
            "ok": False,
            "error": f"No results found for '{need}'. Try a different term.",
        }

    # Step 2: fetch first result
    first_url = results[0].get("url", "")
    fetch_result = fetch_url_text(first_url, max_chars=8000)
    if not fetch_result.get("ok"):
        return {
            "ok": False,
            "error": f"Could not fetch docs: {fetch_result.get('error', 'unknown')}",
        }

    # Step 3: extract examples
    examples = extract_api_usage(fetch_result.get("text", ""))

    # Step 4: synthesize
    tool_name = results[0].get("title", "Unknown")
    synthesis = synthesize_usage(tool_name, examples)

    return {
        "ok": True,
        "search": {
            "query": search_result.get("query", ""),
            "top_result": results[0],
        },
        "fetched": {
            "url": fetch_result.get("url"),
            "title": fetch_result.get("title"),
            "length": fetch_result.get("length"),
        },
        "synthesis": synthesis,
        "generated_at": int(time.time()),
    }


def explain_tool_usage(need: str) -> str:
    """Generate human-readable explanation of tool usage."""
    result = search_tool_and_synthesize(need)
    if not result.get("ok"):
        return f"I couldn't find tools for '{need}': {result.get('error', 'unknown error')}"

    tool = result.get("search", {}).get("top_result", {})
    synthesis = result.get("synthesis", {})
    fetched = result.get("fetched", {})

    parts = [
        f"**Found tool**: {tool.get('title', 'Unknown')}",
        f"**URL**: {tool.get('url', 'N/A')}",
        "",
        "Usage pattern:",
        synthesis.get("pattern", "No pattern generated."),
        "",
        f"**Source docs**: {fetched.get('title', 'N/A')}",
    ]

    return "\n".join(parts)

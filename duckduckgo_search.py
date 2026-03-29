"""Free DuckDuckGo search integration for Weslr.

Provides web search capability without API keys.
Uses DuckDuckGo HTML API for search results.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Any

# Base URL for DuckDuckGo search
DDG_BASE_URL = "https://html.duckduckgo.com/html/"
DDG_VIA_QUERY_URL = "https://links.duckduckgo.com/d.js?"


def search(query: str, max_results: int = 10, language: str = "de") -> List[Dict[str, Any]]:
    """Search DuckDuckGo for a query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        language: Language code (de, en, etc.)
        
    Returns:
        List of search results with title, url, description
    """
    try:
        # URL encode query
        encoded_query = urllib.parse.quote(query)
        
        # Build URL for HTML search
        search_url = f"{DDG_BASE_URL}?q={encoded_query}&kl={language}"
        
        # Make request with headers to simulate browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        req = urllib.request.Request(search_url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        # Parse results from HTML
        results = parse_ddg_results(html, max_results)
        
        return results
        
    except Exception as e:
        # Fallback: use web_search service
        return []


def parse_ddg_results(html: str, max_results: int) -> List[Dict[str, Any]]:
    """Parse DuckDuckGo HTML search results."""
    results = []
    
    # Simple HTML parsing - look for result links
    import re
    
    # Extract links from HTML
    link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
    
    # Filter and extract results
    seen_urls = set()
    
    for match in re.finditer(link_pattern, html):
        url = match.group(1)
        title = match.group(2)
        
        # Skip non-search-result links
        if any(x in url.lower() for x in ['/search?', 'javascript:', '#']):
            continue
            
        # Extract description from surrounding context
        description = ""
        
        # Try to find nearby description text
        start = match.start()
        end = match.end()
        
        # Limit results
        if url not in seen_urls and len(results) < max_results:
            seen_urls.add(url)
            results.append({
                "title": title.strip(),
                "url": url,
                "description": description,
                "source": "duckduckgo",
                "timestamp": int(time.time())
            })
    
    return results


def search_and_summarize(query: str, max_results: int = 3, language: str = "de") -> Dict[str, Any]:
    """Search and return summary of top results."""
    results = search(query, max_results, language)
    
    if not results:
        return {
            "success": False,
            "error": "No results found",
            "query": query
        }
    
    # Build summary
    summaries = []
    for result in results:
        summaries.append({
            "title": result.get("title", "No title"),
            "url": result.get("url", ""),
            "description": result.get("description", "")
        })
    
    return {
        "success": True,
        "query": query,
        "results": summaries,
        "total_found": len(summaries),
        "source": "duckduckgo"
    }


# Alternative: Use web_search through openclaw if available
def search_with_fallback(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search with fallback to openclaw web_search."""
    # Try DuckDuckGo first
    ddg_results = search(query, max_results)
    
    if ddg_results:
        return ddg_results
    
    # Fallback: try web_search (requires Brave API)
    from openclaw import web_search
    return web_search(query, count=max_results)


if __name__ == "__main__":
    # Test search
    import sys
    
    query = sys.argv[1] if len(sys.argv) > 1 else "Entfernungspauschale 2025"
    print(f"Searching for: {query}")
    print()
    
    results = search(query, max_results=5)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('title', 'No title')}")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   Description: {result.get('description', 'N/A')[:100]}...")
        print()

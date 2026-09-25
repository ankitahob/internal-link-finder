import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from crawler.cache import init_db, get_cached_page, save_page

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) InternalLinkFinderBot/1.0"
}

def extract_title_content_links(html, base_url):
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    title = title_tag.text.strip() if title_tag else ""

    # Remove nav/footer/header/aside BEFORE extracting links or text,
    # so only in-content links and text are ever counted.
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    main = soup.find("article") or soup.find("main") or soup.find("body")

    links = set()
    if main:
        for a in main.find_all("a", href=True):
            links.add(urljoin(base_url, a["href"]))

    text = main.get_text(separator=" ", strip=True) if main else ""

    text = re.sub(r"By .*? Team\s*", "", text)
    text = re.sub(r"Published on.*?\d{4}", "", text)
    text = re.sub(r"Last Updated on.*?\d{4}", "", text)
    text = re.sub(r"Table of contents.*?(?=[A-Z][a-z]{3,})", "", text, count=1)

    return title, text.strip(), list(links)


def fetch_page(url, use_cache=True, timeout=15):
    init_db()

    if use_cache:
        cached = get_cached_page(url)
        if cached:
            return cached

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    title, content, links = extract_title_content_links(resp.text, url)
    save_page(url, title, content, links)
    return {"title": title, "content": content, "links": links}


def fetch_pages_parallel(urls, use_cache=True, max_workers=10, progress_callback=None):
    """
    Fetches many URLs concurrently. Cached pages are returned instantly
    (no network call); only uncached URLs are fetched in parallel threads.
    progress_callback(done, total) is called as each page completes.
    Returns a dict: {url: page_data_or_None}
    """
    init_db()
    results = {}
    to_fetch = []

    for url in urls:
        if use_cache:
            cached = get_cached_page(url)
            if cached:
                results[url] = cached
                continue
        to_fetch.append(url)

    done_count = len(results)
    total = len(urls)
    if progress_callback:
        progress_callback(done_count, total)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_page, url, use_cache): url for url in to_fetch}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception:
                results[url] = None
            done_count += 1
            if progress_callback:
                progress_callback(done_count, total)

    return results


if __name__ == "__main__":
    test_url = "https://www.mygreatlearning.com/blog/learn-coding-at-home/"
    result = fetch_page(test_url, use_cache=False)
    if result:
        print(f"\nTitle: {result['title']}")
        print(f"Content length: {len(result['content'])} characters")
        print(f"Links found: {len(result['links'])}")
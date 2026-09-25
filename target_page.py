import requests
from bs4 import BeautifulSoup
from crawler.page_fetcher import HEADERS

def analyze_target_page(url, timeout=15):
    """
    Crawls the target page and extracts title, headings, and main content.
    Not cached — this is your own page, so it's cheap to fetch fresh each run.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Failed: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    title_tag = soup.find("title")
    title = title_tag.text.strip() if title_tag else ""

    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    main = soup.find("article") or soup.find("main") or soup.find("body")
    content = main.get_text(separator=" ", strip=True) if main else ""

    return {
        "url": url,
        "title": title,
        "h1": h1_tags,
        "h2": h2_tags,
        "h3": h3_tags,
        "content": content,
    }


if __name__ == "__main__":
    test_url = "https://degrees.srmonline.in/online-mba-srm"
    result = analyze_target_page(test_url)
    if result:
        print(f"\nTitle: {result['title']}")
        print(f"H1: {result['h1']}")
        print(f"Content length: {len(result['content'])} characters")
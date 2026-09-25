import requests
from bs4 import BeautifulSoup

def get_urls_from_sitemap(sitemap_url, seen=None):
    """
    Fetches a sitemap URL. If it's a sitemap INDEX (lists other sitemaps),
    recursively fetches each one. Returns a flat list of all page URLs found.
    """
    if seen is None:
        seen = set()

    if sitemap_url in seen:
        return []
    seen.add(sitemap_url)

    print(f"Fetching: {sitemap_url}")

    try:
        response = requests.get(sitemap_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Failed to fetch {sitemap_url}: {e}")
        return []

    soup = BeautifulSoup(response.content, "xml")

    sitemap_tags = soup.find_all("sitemap")
    if sitemap_tags:
        all_urls = []
        for tag in sitemap_tags:
            loc = tag.find("loc")
            if loc and loc.text:
                child_urls = get_urls_from_sitemap(loc.text.strip(), seen)
                all_urls.extend(child_urls)
        return all_urls

    url_tags = soup.find_all("url")
    urls = []
    for tag in url_tags:
        loc = tag.find("loc")
        if loc and loc.text:
            urls.append(loc.text.strip())

    return urls


if __name__ == "__main__":
    test_sitemap = "https://www.mygreatlearning.com/blog/sitemap_index.xml"
    urls = get_urls_from_sitemap(test_sitemap)
    print(f"\nTotal URLs found: {len(urls)}")
    for u in urls[:20]:
        print(u)
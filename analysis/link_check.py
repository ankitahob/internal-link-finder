from urllib.parse import urlparse

def normalize_url(url):
    """
    Normalizes a URL so http/https, www/no-www, and trailing slash
    differences don't cause false negatives.
    """
    parsed = urlparse(url.strip().lower())
    netloc = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip("/")
    return f"{netloc}{path}"

def already_links_to_target(blog_links, target_url):
    """
    Returns True if any link in blog_links points to target_url
    (after normalization).
    """
    target_normalized = normalize_url(target_url)
    for link in blog_links:
        if normalize_url(link) == target_normalized:
            return True
    return False
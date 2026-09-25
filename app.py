import streamlit as st
import pandas as pd
from io import BytesIO

from crawler.sitemap import get_urls_from_sitemap
from crawler.page_fetcher import fetch_pages_parallel
from analysis.target_page import analyze_target_page
from analysis.relevance import rank_blogs_by_relevance
from analysis.link_check import already_links_to_target
from analysis.keyword_match import classify_match

st.set_page_config(page_title="Internal Link Finder", layout="wide")
st.title("🔗 Internal Linking Opportunity Finder")

with st.form("inputs"):
    col1, col2 = st.columns(2)
    with col1:
        sitemap_url = st.text_input("Sitemap URL", placeholder="https://example.com/blog/sitemap_index.xml")
        target_url = st.text_input("Target Page URL", placeholder="https://example.com/online-mba")
    with col2:
        keywords_raw = st.text_input("Target Keyword(s) — comma separated", placeholder="online MBA, MBA program")
        max_blogs = st.number_input("Max blogs to crawl (for speed)", min_value=5, max_value=2000, value=100, step=5)

    col3, col4 = st.columns(2)
    with col3:
        min_score = st.slider("Minimum relevance score", 0, 100, 40)
    with col4:
        max_results = st.number_input("Max results to show", min_value=5, max_value=2000, value=50)

    submitted = st.form_submit_button("Find Internal Linking Opportunities")

if submitted:
    if not sitemap_url or not target_url or not keywords_raw:
        st.error("Please fill in sitemap URL, target URL, and at least one keyword.")
        st.stop()

    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

    with st.spinner("Analyzing target page..."):
        target = analyze_target_page(target_url)
        if not target:
            st.error("Could not fetch the target page. Check the URL.")
            st.stop()

    st.success(f"Target page: **{target['title']}**")

    with st.spinner("Fetching sitemap..."):
        all_urls = get_urls_from_sitemap(sitemap_url)

    st.info(f"Found {len(all_urls)} URLs in sitemap. Crawling up to {max_blogs} of them...")

    urls_to_crawl = all_urls[:max_blogs]
    crawl_progress = st.progress(0)
    crawl_status = st.empty()

    def update_crawl_progress(done, total):
        crawl_progress.progress(done / total)
        crawl_status.text(f"Crawling: {done}/{total}")

    fetched = fetch_pages_parallel(urls_to_crawl, progress_callback=update_crawl_progress)
    blogs = [
        {"url": url, "title": p["title"], "content": p["content"], "links": p.get("links", [])}
        for url, p in fetched.items() if p
    ]

    crawl_progress.empty()
    crawl_status.empty()
    st.success(f"Crawled {len(blogs)} pages successfully.")

    relevance_progress = st.progress(0)
    relevance_status = st.empty()

    def update_relevance_progress(current, total):
        relevance_progress.progress(current / total)
        relevance_status.text(f"Scoring relevance: {current}/{total}")

    ranked = rank_blogs_by_relevance(
        target["title"], target["content"], blogs,
        progress_callback=update_relevance_progress
    )
    relevance_progress.empty()
    relevance_status.empty()

    results = []
    for blog in ranked:
        if blog["relevance_score"] < min_score:
            continue

        already_linked = already_links_to_target(blog.get("links", []), target_url)

        if already_linked:
            match_type = "Already Linked"
            matched_sentence = ""
        else:
            best_match = {"match_type": "none", "matched_sentence": None}
            for kw in keywords:
                m = classify_match(blog["content"], kw)
                if m["match_type"] == "exact":
                    best_match = m
                    break
                elif m["match_type"] == "broad" and best_match["match_type"] == "none":
                    best_match = m
            match_type = best_match["match_type"]
            matched_sentence = best_match.get("matched_sentence") or ""

        priority = "High" if blog["relevance_score"] >= 70 and match_type != "none" and not already_linked else \
                   "Medium" if blog["relevance_score"] >= min_score and not already_linked else "Low"

        results.append({
            "Blog URL": blog["url"],
            "Blog Title": blog["title"],
            "Relevance Score": blog["relevance_score"],
            "Already Linked": "Yes" if already_linked else "No",
            "Match Type": match_type,
            "Matched Sentence": matched_sentence,
            "Priority": priority,
        })

        if len(results) >= max_results:
            break

    if not results:
        st.warning("No opportunities found above the relevance threshold. Try lowering it.")
    else:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "internal_link_opportunities.csv", "text/csv")

        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        st.download_button("⬇️ Download Excel", excel_buffer.getvalue(), "internal_link_opportunities.xlsx")
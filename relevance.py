from sentence_transformers import SentenceTransformer, util
import torch

_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading embedding model (first time may take a minute)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def build_text_for_embedding(title, content, max_chars=2500):
    cleaned = content[100:100 + max_chars]
    return f"{title}. {title}. {cleaned}"


def rank_blogs_by_relevance(target_title, target_content, blogs, progress_callback=None):
    """
    progress_callback: optional function(current, total) for live UI progress.
    """
    model = get_model()

    target_text = build_text_for_embedding(target_title, target_content)
    target_embedding = model.encode(target_text, convert_to_tensor=True)

    blog_texts = [
        build_text_for_embedding(b["title"], b["content"]) for b in blogs
    ]

    batch_size = 32
    all_embeddings = []
    for i in range(0, len(blog_texts), batch_size):
        batch = blog_texts[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_tensor=True)
        all_embeddings.append(batch_embeddings)
        if progress_callback:
            progress_callback(min(i + batch_size, len(blog_texts)), len(blog_texts))

    blog_embeddings = torch.cat(all_embeddings, dim=0) if all_embeddings else torch.empty(0)

    similarities = util.cos_sim(target_embedding, blog_embeddings)[0]

    for blog, score in zip(blogs, similarities):
        blog["relevance_score"] = round(float(score) * 100, 1)

    return sorted(blogs, key=lambda b: b["relevance_score"], reverse=True)
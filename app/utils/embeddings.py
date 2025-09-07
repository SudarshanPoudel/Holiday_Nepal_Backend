from sentence_transformers import SentenceTransformer

def get_embedding(text: str) -> list[float]:
    model = SentenceTransformer("all-MiniLM-L6-v2")

    if not text:
        return [0.0] * 384  
    return model.encode(text, convert_to_numpy=True).tolist()

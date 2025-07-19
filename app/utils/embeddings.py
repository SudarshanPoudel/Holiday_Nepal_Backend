from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dim output

def get_embedding(text: str) -> list[float]:
    if not text:
        return [0.0] * 384  
    return model.encode(text, convert_to_numpy=True).tolist()

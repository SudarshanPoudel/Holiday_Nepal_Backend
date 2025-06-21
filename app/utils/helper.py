import re
import unicodedata

def slugify(text: str) -> str:
    if text is None:
        return None
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text

def symmetric_pair(a: int, b: int) -> int:
    a, b = sorted((a, b))
    return (a + b) * (a + b + 1) // 2 + b

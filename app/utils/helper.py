import re
import unicodedata
from sqlalchemy.orm import DeclarativeMeta
import json
from sqlalchemy.orm.state import InstanceState

def slugify(text: str) -> str:
    if text is None:
        return None
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text

def symmetric_pair(a: int, b: int) -> int:
    return (a + b) * (a + b + 1) // 2 + b



def to_dict(obj, visited=None):
    if visited is None:
        visited = set()

    if isinstance(obj.__class__, DeclarativeMeta):
        obj_id = id(obj)
        if obj_id in visited:
            return f"<CircularRef: {obj.__class__.__name__}>"
        visited.add(obj_id)

        fields = {}

        # Serialize columns
        for field in obj.__table__.columns.keys():
            value = getattr(obj, field)
            try:
                json.dumps(value)
                fields[field] = value
            except:
                fields[field] = str(value)

        # Serialize only *loaded* relationships
        state: InstanceState = obj.__dict__.get('_sa_instance_state')
        if state:
            for rel in obj.__mapper__.relationships.keys():
                if rel in state.dict:  # Only if it's loaded
                    related = getattr(obj, rel)
                    if related is None:
                        fields[rel] = None
                    elif isinstance(related, list):
                        fields[rel] = [to_dict(i, visited) for i in related]
                    else:
                        fields[rel] = to_dict(related, visited)

        return fields

    return str(obj)
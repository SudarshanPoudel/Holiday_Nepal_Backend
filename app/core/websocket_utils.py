

from datetime import datetime
import json

from fastapi import HTTPException, WebSocket, status

from app.modules.auth.service import AuthService


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'dict'):
        return obj.dict()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def safe_json_dumps(data):
    """Safely serialize data to JSON with custom serializer"""
    return json.dumps(data, default=json_serializer)

async def authenticate_websocket(websocket: WebSocket) -> int:
    token = websocket.query_params.get("token")
    if token:
        try:
            user_data = AuthService.verify_access_token(token)  
            return user_data.get("user_id")
        except Exception as e:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    
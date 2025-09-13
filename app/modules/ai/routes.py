from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
import traceback
from app.core.schemas import BaseResponse
from app.database.redis_cache import RedisCache, get_redis_cache
from app.modules.ai.controller import AIController
from app.utils.websocket_utils import authenticate_websocket, safe_json_dumps
from app.database.database import get_db
from app.database.graph_database import get_graph_db
from app.modules.auth.service import AuthService


router = APIRouter()

@router.websocket("/generate")
async def generate_plan_websocket(
    websocket: WebSocket, 
    db = Depends(get_db), 
    graph_db = Depends(get_graph_db),
    redis: RedisCache = Depends(get_redis_cache("chat")),
):
    await websocket.accept()
    try:
        user_id = await authenticate_websocket(websocket)
        
        if user_id is None:
            await websocket.send_text(safe_json_dumps({
                "type": "error",
                "message": "Token is required"
            }))
            return
            
        data = await websocket.receive_json()
        prompt = data.get("prompt")
        
        if not prompt:
            await websocket.send_text(safe_json_dumps({
                "type": "error",
                "message": "Missing prompt"
            }))
            return
            
        controller = AIController(db, graph_db, redis, user_id)
        await controller.generate_plan_websocket(prompt, websocket)
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        traceback.print_exc()
        await websocket.send_text(safe_json_dumps({
            "type": "error", 
            "message": str(e)
        }))
    finally:
        await websocket.close()


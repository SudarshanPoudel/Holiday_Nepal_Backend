from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
import traceback
from app.core.schemas import BaseResponse
from app.database.redis_cache import RedisCache, get_redis_cache
from app.modules.ai.cache import AICache
from app.modules.ai.controller import AIController
from app.core.websocket_utils import authenticate_websocket, safe_json_dumps
from app.database.database import get_db
from app.database.graph_database import get_graph_db
from app.modules.auth.service import AuthService


router = APIRouter()

@router.get("/{plan_id}")
async def get_chat(
    plan_id: int, 
    request: Request, 
    redis: RedisCache = Depends(get_redis_cache("chat")),
):
    try:
        user_id = request.state.user_id
        cache = AICache(redis)
        data = await cache.get(user_id, plan_id)
        if not data:
            raise HTTPException(status_code=404, detail="Chat not found")
        return BaseResponse(message="Chat fetched successfully", data=data)
    except HTTPException as e:
        raise e
    except Exception as e:        
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

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


    
@router.websocket("/{plan_id}")
async def edit_plan(
    websocket: WebSocket,  
    plan_id: int, 
    db = Depends(get_db), 
    graph_db = Depends(get_graph_db),
    redis: RedisCache = Depends(get_redis_cache("chat")),
):
    await websocket.accept()
    try:
        user_id = await authenticate_websocket(websocket)
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        data = await websocket.receive_json()
        prompt = data.get("prompt")
        if not prompt:
            await websocket.send_text(safe_json_dumps({
                "type": "error",
                "message": "Missing prompt"
            }))
            return
        
        await websocket.send_text(safe_json_dumps({
            "type": "prompt",
            "response": prompt
        }))
        
        controller = AIController(db, graph_db, redis, user_id)
        return await controller.edit_plan(plan_id, prompt, websocket)
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

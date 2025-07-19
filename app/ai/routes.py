from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
import traceback
from app.ai.controller import AIController
from app.core.websocket_utils import authenticate_websocket, safe_json_dumps
from app.database.database import get_db
from app.database.graph_database import get_graph_db
from app.modules.auth.service import AuthService


router = APIRouter()


@router.websocket("/generate-plan")
async def generate_plan_websocket(
    websocket: WebSocket, 
    db = Depends(get_db), 
    graph_db = Depends(get_graph_db)
):
    await websocket.accept()
    try:
        user_id = await authenticate_websocket(websocket)
        
        if user_id is None:
            # If no auth found, expect first message to contain auth info
            await websocket.send_text(safe_json_dumps({
                "type": "auth_required",
                "message": "Please send authentication token"
            }))
            
            # Wait for auth message
            auth_data = await websocket.receive_text()
            auth_request = json.loads(auth_data)
            
            token = auth_request.get("token")
            if not token:
                await websocket.send_text(safe_json_dumps({
                    "type": "error",
                    "message": "Token is required"
                }))
                return
            
            try:
                user_data = AuthService.verify_access_token(token)
                user_id = user_data.get("user_id")
            except Exception as e:
                await websocket.send_text(safe_json_dumps({
                    "type": "error",
                    "message": "Invalid authentication token"
                }))
                return
            
            # Now wait for the actual request
            data = await websocket.receive_text()
            request_data = json.loads(data)
        else:
            # User already authenticated, get the request data
            data = await websocket.receive_text()
            request_data = json.loads(data)
        
        prompt = request_data.get("prompt")
        
        if not prompt:
            await websocket.send_text(safe_json_dumps({
                "type": "error",
                "message": "Missing prompt"
            }))
            return
            
        controller = AIController(db, graph_db, user_id)
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


    
@router.put("/edit-plan/{plan_id}")
async def edit_plan(request: Request, plan_id: int, prompt: str, db = Depends(get_db), graph_db = Depends(get_graph_db)):
    try:
        user_id = request.state.user_id
        controller = AIController(db, graph_db, user_id)
        return await controller.edit_plan(plan_id, prompt)
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
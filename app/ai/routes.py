from fastapi import APIRouter, Depends, HTTPException, Request
import traceback
from app.ai.controller import AIController
from app.database.database import get_db
from app.database.graph_database import get_graph_db


router = APIRouter()

@router.post("/generate-plan")
async def generate_plan(request: Request, prompt: str, db = Depends(get_db), graph_db = Depends(get_graph_db)):
    try:
        user_id = request.state.user_id
        controller = AIController(db, graph_db, user_id)
        return await controller.generate_plan(prompt)
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
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
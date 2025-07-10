from fastapi import Request, HTTPException

def require_admin(request: Request):
    if request.state.role != "admin":
        raise HTTPException(status_code=403, detail="You must be an admin to perform this action.")

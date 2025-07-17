from fastapi import Depends, Request, HTTPException

def require_admin(request: Request):
    def checker(request: Request):
        role = getattr(request.state, "role", None)
        if role != "admin":
            raise HTTPException(status_code=403, detail="You must be an admin to perform this action.")
    return Depends(checker)

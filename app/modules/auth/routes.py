from fastapi import APIRouter, Depends, Request, Response
from app.modules.auth.controller import AuthController
from app.modules.auth.schemas import UserLogin, UserRegister
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
controller = AuthController()

@router.post("/register")
async def register(user_register: UserRegister, db: AsyncSession = Depends(get_db)):
    return await controller.register(user_register, db)

@router.post("/login")
async def login(user_login: UserLogin, response:Response, db: AsyncSession = Depends(get_db)):
    return await controller.login(user_login, db, response)

@router.get("/me")
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = int(request.state.user_id)
    return await controller.me(user_id, db)

@router.delete("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    return await controller.logout(request, response, db)

@router.post("/verify_email")
async def verify_email(email:str, otp:str, db: AsyncSession = Depends(get_db)):
    return await controller.verify_email(email, otp, db)

@router.post("/resend_otp")
async def resend_verification_code(email:str):
    return await controller.resend_verification_code(email)

@router.post("/refresh_token")
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    return await controller.refresh_token(request, response, db)

@router.post("/forget_password")
async def forget_password(email:str, db: AsyncSession = Depends(get_db)):
    return await controller.forget_password(email, db)

@router.post("/reset_password")
async def reset_password(token: str, new_password: str, db: AsyncSession= Depends(get_db)):
    return await controller.reset_password(token, new_password, db)

@router.post("/change_password")
async def change_password(request: Request, old_password:str, new_password: str, db: AsyncSession = Depends(get_db)):
    user_id = int(request.state.user_id)
    return await controller.change_password(user_id, old_password, new_password, db)

@router.get("/oauth/google")
async def google_login():
    return await controller.google_login_url()


@router.post("/oauth/google/callback")
async def google_callback(code: str, response: Response, db: AsyncSession = Depends(get_db)):
    return await controller.handle_google_callback(code, db, response)

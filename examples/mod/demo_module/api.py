from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user_from_token

router = APIRouter(prefix="/demo", tags=["demo"])

@router.get("/hello")
async def hello(name: str = "World", user=Depends(get_current_user_from_token)):
    return {"message": f"Hello {name} from demo module", "user": user["username"]}

@router.post("/echo")
async def echo(data: dict, user=Depends(get_current_user_from_token)):
    return {"echo": data}
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/me")
async def get_current_user():
    return {"message": "Get current user - to be implemented"}

@router.patch("/users/me")
async def update_current_user():
    return {"message": "Update current user - to be implemented"}

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    return {"message": f"Get user {user_id} - to be implemented"}

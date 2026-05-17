from fastapi import Request, HTTPException
from typing import Dict

async def get_current_user(request: Request) -> Dict:
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_role = request.headers.get("X-User-Role")
    return {"user_id": user_id, "role": user_role}
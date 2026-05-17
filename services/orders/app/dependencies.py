from fastapi import HTTPException, Request
from typing import Dict

async def get_current_user(request: Request) -> Dict:
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    role = request.headers.get("X-User-Role")
    return {"user_id": user_id, "role": role}

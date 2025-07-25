from typing import Optional

from fastapi import Depends, HTTPException,Header
from app.shared.handles.jwt_user import verify_jwt
from fastapi.security import HTTPBearer

security = HTTPBearer()  # Define o esquema de segurança Bearer

def get_current_user( token: Optional[str]  = Header(None) ):
    """
    Verifica o JWT se o Authorization header for fornecido.
    """
    if token:
        try:
            payload = verify_jwt(token)
            user_id: str = payload.get("id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token: user ID not found")
            return {"user_id": user_id, "payload": payload}
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

    return None

from fastapi import Depends, HTTPException, status
from core.auth import get_current_user


def admin_required(current_user: dict = Depends(get_current_user)):
    """
    Ensures only admin users can access the endpoint.
    """
    user = current_user["user"]
    if user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admins only."
        )
    return current_user


def user_required(current_user: dict = Depends(get_current_user)):
    """
    Ensures only normal users can access the endpoint.
    """
    user = current_user["user"]
    if user.role.value != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Users only."
        )
    return current_user

def admin_or_user_required(current_user: dict = Depends(get_current_user)):
    """
    Ensures only admin or normal users can access the endpoint.
    """
    user = current_user["user"]
    if user.role.value not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admins or Users only."
        )
    return current_user
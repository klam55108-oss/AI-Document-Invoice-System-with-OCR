"""API dependencies for authorization and shared context."""

from fastapi import Header, HTTPException, status


def require_operator_or_maintainer(x_user_role: str | None = Header(default=None, alias="X-User-Role")) -> str:
    """Allow only operator or maintainer roles."""
    if not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role required",
        )

    normalized_role = x_user_role.strip().lower()
    if normalized_role not in {"operator", "maintainer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return normalized_role

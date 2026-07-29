from typing import Any, Dict, Optional

def format_response(status: str, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Standardize the API response format across all Nexora AI routes.
    """
    return {
        "status": status,
        "message": message,
        "data": data or {}
    }

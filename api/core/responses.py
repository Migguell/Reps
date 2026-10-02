from typing import Any, Optional
from flask import jsonify, Response


def success(data: Any = None, message: str = "Operation completed successfully.", status_code: int = 200) -> tuple[Response, int]:
    return jsonify({"data": data, "message": message}), status_code


def created(data: Any = None, message: str = "Resource created successfully.") -> tuple[Response, int]:
    return success(data, message, 201)


def error(message: str, status_code: int = 400, details: Optional[Any] = None) -> tuple[Response, int]:
    body: dict[str, Any] = {"error": message, "status_code": status_code}
    if details is not None:
        body["details"] = details
    return jsonify(body), status_code


def not_found(resource: str = "Resource") -> tuple[Response, int]:
    return error(f"{resource} not found.", 404)


def internal_error(message: str = "Internal server error.") -> tuple[Response, int]:
    return error(message, 500)

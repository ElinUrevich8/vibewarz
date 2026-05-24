"""Encode/decode protocol messages as JSON over the wire.

Both directions are symmetric:
  - server uses `decode_client` / `safe_decode_client` for inbound frames and
    `encode_server` for outbound
  - SDK client uses `decode_server` / `safe_decode_server` for inbound and
    `encode_client` for outbound
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter, ValidationError

from .messages import ClientMessage, ServerMessage

_client_adapter: TypeAdapter[Any] = TypeAdapter(ClientMessage)
_server_adapter: TypeAdapter[Any] = TypeAdapter(ServerMessage)


def decode_client(raw: str | bytes) -> Any:
    """Parse a JSON frame from the client. Raises ValidationError on bad shape."""
    data = json.loads(raw)
    return _client_adapter.validate_python(data)


def encode_server(msg: Any) -> str:
    """Serialize a server message to JSON text."""
    return _server_adapter.dump_json(msg).decode()


def safe_decode_client(raw: str | bytes) -> tuple[Any | None, str | None]:
    """Like decode_client but returns (None, error_message) on failure
    instead of raising. Useful in the WS loop where we want to send back an
    `ErrorS2C` rather than tear down the socket."""
    try:
        return decode_client(raw), None
    except (json.JSONDecodeError, ValidationError) as e:
        return None, str(e)


def decode_server(raw: str | bytes) -> Any:
    """Parse a JSON frame from the server. Raises ValidationError on bad shape."""
    data = json.loads(raw)
    return _server_adapter.validate_python(data)


def encode_client(msg: Any) -> str:
    """Serialize a client message to JSON text."""
    return _client_adapter.dump_json(msg).decode()


def safe_decode_server(raw: str | bytes) -> tuple[Any | None, str | None]:
    """Like decode_server but returns (None, error_message) on failure."""
    try:
        return decode_server(raw), None
    except (json.JSONDecodeError, ValidationError) as e:
        return None, str(e)

from __future__ import annotations

import json
from typing import Any, Optional
from uuid import uuid4

import requests
from requests import Response, Session
from requests.exceptions import JSONDecodeError, RequestException


class GenerativeError(Exception):
    """Base exception for Generative client."""


class APIResponseError(GenerativeError):
    """Raised when API returns an invalid response."""


class Generative:
    API_URL = "https://chat.openai.com/backend-api/conversation"
    MODEL = "text-davinci-002-render-sha"

    def __init__(
        self,
        access_token: str,
        history_and_training_enabled: bool = False,
        logging: bool = False,
        timeout: int = 60,
    ) -> None:
        self.access_token = access_token
        self.history_and_training_enabled = (
            history_and_training_enabled
        )
        self.logging = logging
        self.timeout = timeout

        self.session: Session = requests.Session()

        self.session.headers.update(
            {
                "user-agent": "node",
                "accept": "text/event-stream",
                "accept-language": "en-US",
                "authorization": f"Bearer {access_token}",
                "content-type": "application/json",
                "referer": "https://chat.openai.com/",
            }
        )

    def _build_payload(
        self,
        text: str,
    ) -> dict[str, Any]:
        return {
            "action": "next",
            "arkose_token": None,
            "conversation_mode": {
                "kind": "primary_assistant",
            },
            "force_paragen": False,
            "force_rate_limit": False,
            "history_and_training_disabled": (
                not self.history_and_training_enabled
            ),
            "messages": [
                {
                    "metadata": {},
                    "author": {
                        "role": "user",
                    },
                    "content": {
                        "content_type": "text",
                        "parts": [text],
                    },
                }
            ],
            "model": self.MODEL,
            "parent_message_id": str(uuid4()),
            "timezone_offset_min": -330,
        }

    def _parse_stream_response(
        self,
        response_text: str,
    ) -> dict[str, Any]:
        parsed_data: Optional[dict[str, Any]] = None

        for line in response_text.splitlines():
            if not line.startswith('data: {"message":'):
                continue

            try:
                parsed_data = json.loads(line[6:])
            except JSONDecodeError as error:
                raise APIResponseError(
                    "Failed to decode assistant response JSON."
                ) from error

        if parsed_data is None:
            raise APIResponseError(
                "No valid assistant response found."
            )

        return parsed_data

    def _validate_message(
        self,
        data: dict[str, Any],
    ) -> list[str]:
        message = data.get("message")

        if not message:
            raise APIResponseError(
                "Missing message object in response."
            )

        if (
            message.get("status")
            != "finished_successfully"
        ):
            raise APIResponseError(
                "Assistant response did not finish successfully."
            )

        content = message.get("content", {})

        if content.get("content_type") != "text":
            raise APIResponseError(
                "Expected text content from assistant."
            )

        parts = content.get("parts")

        if not isinstance(parts, list):
            raise APIResponseError(
                "Invalid response parts format."
            )

        return parts

    def _log_response(
        self,
        response_text: str,
    ) -> None:
        if not self.logging:
            return

        with open(
            "chatgpt-response.txt",
            "w",
            encoding="utf-8",
        ) as file:
            file.write(response_text)

    def prompt(self, text: str) -> str:
        payload = self._build_payload(text)

        try:
            response: Response = self.session.post(
                url=self.API_URL,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except RequestException as error:
            raise GenerativeError(
                f"Request failed: {error}"
            ) from error

        self._log_response(response.text)

        data = self._parse_stream_response(
            response.text
        )

        message_parts = self._validate_message(
            data
        )

        return "".join(message_parts)

from __future__ import annotations

import json
from typing import Any, Optional
from uuid import uuid4

import requests
from requests import Response, Session
from requests.exceptions import JSONDecodeError, RequestException


class ConversationError(Exception):
    """Base exception for conversation errors."""


class InvalidResponseError(ConversationError):
    """Raised when the API response is invalid."""


class Conversation:
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

        self.conversation_id: Optional[str] = None

        self.session: Session = requests.Session()

        self.session.headers.update(
            {
                "user-agent": "node",
                "accept": "text/event-stream",
                "accept-language": "en-US",
                "authorization": f"Bearer {self.access_token}",
                "content-type": "application/json",
                "referer": "https://chat.openai.com",
            }
        )

    def _build_request_body(self, text: str) -> dict[str, Any]:
        body: dict[str, Any] = {
            "action": "next",
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

        if self.conversation_id:
            body["conversation_id"] = self.conversation_id

        return body

    def _extract_response_data(
        self,
        response_text: str,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {}

        for chunk in response_text.splitlines():
            if not chunk.startswith('data: {"message":'):
                continue

            try:
                data = json.loads(chunk[6:])
            except JSONDecodeError as error:
                raise InvalidResponseError(
                    "Failed to parse assistant response JSON."
                ) from error

        if not data:
            raise InvalidResponseError(
                "No valid assistant response received."
            )

        return data

    def _validate_response(
        self,
        data: dict[str, Any],
    ) -> list[str]:
        message = data.get("message", {})

        if (
            message.get("status")
            != "finished_successfully"
        ):
            raise InvalidResponseError(
                "Assistant response was not completed successfully."
            )

        content = message.get("content", {})

        if content.get("content_type") != "text":
            raise InvalidResponseError(
                "Expected text response from assistant."
            )

        parts = content.get("parts", [])

        if not isinstance(parts, list):
            raise InvalidResponseError(
                "Invalid response content format."
            )

        return parts

    def prompt(self, text: str) -> str:
        body = self._build_request_body(text)

        try:
            response: Response = self.session.post(
                url=self.API_URL,
                json=body,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except RequestException as error:
            raise ConversationError(
                f"Request failed: {error}"
            ) from error

        if self.logging:
            with open(
                "chatgpt-response.txt",
                "w",
                encoding="utf-8",
            ) as file:
                file.write(response.text)

        data = self._extract_response_data(response.text)

        conversation_id = data.get("conversation_id")

        if conversation_id:
            self.conversation_id = conversation_id

        message_parts = self._validate_response(data)

        return "".join(message_parts)

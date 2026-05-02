"""
Filename: ChatMessage.py
Author: Rahul Pothineni
Date: 2026-04-29
Description: Shared TypedDict contract for a raw chat message as it travels
from the EventSub listener through Kafka to downstream consumers.

Fields:
    broadcaster_channel: login of the channel the message was sent in.
    sending_user: login of the user who posted the message.
    message: raw chat message text.
"""

from typing import TypedDict

class ChatMessage(TypedDict):
    session_id: str
    broadcaster_channel: str
    sending_user: str
    message: str
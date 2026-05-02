"""
Filename: eventsub_listener.py
Author: Rahul Pothineni
Date: 2026-04-29
Description: Owns the Twitch EventSub websocket lifecycle. Subscribes the bot
to chat messages for a list of target channels and forwards each event into a
caller-supplied sink (e.g. KafkaProducer.produce) as a ChatMessage dict.
"""

from typing import Callable

from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import ChannelChatMessageEvent
from twitchAPI.twitch import Twitch
from twitchAPI.object.api import TwitchUser

from twitch_ingester_backend.twitch_ingestion.schemas.ChatMessage import ChatMessage
from db.models import Session

class ChatListener:
    def __init__(self, twitch: Twitch, me_id: str, on_message: Callable[[ChatMessage], None], session_id: str): 
        self.twitch = twitch
        self.me_id = me_id
        self.session_id = session_id
        self.on_message = on_message
        self._eventsub: EventSubWebsocket | None = None

    async def on_chat(self, data: ChannelChatMessageEvent):
        """EventSub callback: shape the raw event into a ChatMessage and hand it to the sink."""
        e = data.event
        self.on_message({
            "broadcaster_channel": e.broadcaster_user_login,
            "sending_user": e.chatter_user_login,
            "message": e.message.text,
            "session_id": self.session_id,
        })

    async def start(self, targets: list[TwitchUser]):
        """Open one shared websocket and subscribe to chat for every target channel."""
        self._eventsub = EventSubWebsocket(self.twitch)
        self._eventsub.start()
        for target in targets:
            print(f"monitoring: {target.login} (id={target.id})")
            await self._eventsub.listen_channel_chat_message(
                target.id, self.me_id, self.on_chat
            )

    async def stop(self):
        """Close the websocket if it was started."""
        if self._eventsub:
            await self._eventsub.stop()
"""
Filename: main.py
Author: Rahul Pothineni
Date: 2026-04-29
Description: Entry point for the Twitch chat ingester. Authenticates with Twitch,
opens an EventSub websocket for the configured target channels, and forwards every
chat message to a Kafka topic for downstream consumers.
"""

import os
import asyncio
import certifi

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

from twitch_ingestion.config import load_settings
from twitch_ingestion.kafka_producer import KafkaProducer
from twitch_ingestion.twitch_client import authenticate, resolve_target_channels
from twitch_ingestion.eventsub_listener import ChatListener
from django.utils import timezone
from db.models import Session

# Point aiohttp/SSL at certifi's CA bundle so Twitch API calls succeed on macOS.
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["SSL_CERT_DIR"] = os.path.dirname(certifi.where())

async def run(): 
    """
    Wire up settings -> Twitch auth -> Kafka producer -> EventSub listener and idle until Ctrl+C.
    """
    settings = load_settings()

    #Init new Session object
    session = await Session.objects.acreate()


    twitch, me = await authenticate(settings.app_id, settings.app_secret)
    targets = await resolve_target_channels(twitch, settings.target_channels, session)
    print(f"authed as: {me.login}")
    
    with KafkaProducer(settings.kafka_broker, settings.raw_topic) as producer:
        chat_listener = ChatListener(twitch, me.id, producer.produce, str(session.id))
        await chat_listener.start(targets)

        # EventSub runs its own background task; the main coroutine just parks here
        # so the producer + websocket stay alive until the user interrupts.
        print("listening — press Ctrl+C to stop")
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await chat_listener.stop()
            await twitch.close()
    session.end_time = timezone.now()
    await session.asave()


if __name__ == "__main__":
    asyncio.run(run())
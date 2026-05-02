"""
Filename: config.py
Author: Rahul Pothineni
Date: 2026-04-29
Description: Loads runtime configuration from environment variables (.env) into a
typed Settings dataclass shared across the producer, consumer, and Twitch client.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

@dataclass
class Settings:
    app_id: str
    app_secret: str
    target_channels: list[str]
    kafka_broker: str = "localhost:9092"
    raw_topic: str = "twitch_chat"

def load_settings() -> Settings:
    """Read .env into the process and return a populated Settings instance."""
    load_dotenv()
    return Settings(
        app_id=os.getenv("TWITCH_APP_ID"),
        app_secret=os.getenv("TWITCH_APP_SECRET"),
        target_channels=os.getenv("TARGET_CHANNELS").split(","),
    )

"""
Filename: sentiment.py
Author: Rahul Pothineni
Date: 2026-04-29
Description: Kafka consumer entry point that reads raw chat messages off the
twitch_chat topic and scores them with a roBERTa sentiment model. Messages
are buffered and classified in batches on the fastest available accelerator
(Apple MPS > NVIDIA CUDA > CPU) for higher throughput.

Model: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
"""


import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
django.setup()

import time

import torch
from transformers import pipeline

from twitch_ingester_backend.twitch_ingestion import config
from twitch_ingester_backend.twitch_ingestion.kafka_consumer import KafkaConsumer

from db.models import Streamer, Message
from django.core.exceptions import ObjectDoesNotExist

MODEL_PATH = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Up to BATCH_SIZE messages are classified in a single forward pass; the loop
# never waits longer than MAX_BATCH_WAIT_SECONDS to flush a partial batch.
BATCH_SIZE = 32
MAX_BATCH_WAIT_SECONDS = 0.5


def _pick_device() -> str | int:
    """Select the fastest accelerator available at startup."""
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return 0
    return -1


class Sentiment:
    def __init__(self):
        self.msg_count = 0
        self.settings = config.load_settings()
        device = _pick_device()
        print(f"sentiment device: {device}")
        # Pipeline owns its own model + tokenizer load; passing batch_size lets
        # the pipeline shard long inputs internally if we ever pass more than
        # BATCH_SIZE at once.
        self.sentiment_task = pipeline(
            "sentiment-analysis",
            model=MODEL_PATH,
            device=device,
            batch_size=BATCH_SIZE,
        )

    def classify_batch(self, messages: list[str]):
        """Run a batch of messages through the model in a single forward pass."""
        return self.sentiment_task(messages)

    def run(self):
        """Drain the Kafka consumer in batches and classify each batch in one ML pass."""
        with KafkaConsumer(self.settings) as consumer:
            while True:
                buffer = self._drain_buffer(consumer)
                if not buffer:
                    continue

                messages = [p["message"] for p in buffer]
                results = self.classify_batch(messages)

                for payload, result in zip(buffer, results):
                    self.msg_count += 1
                    session_id = payload.get("session_id")
                    if not session_id:
                        continue
                    try:
                        streamer = Streamer.objects.get(
                            session_id=session_id,
                            username=payload["broadcaster_channel"],
                        )
                    except ObjectDoesNotExist:
                        print(f"no streamer row for {payload['broadcaster_channel']} in session {payload['session_id']}; skipping")
                        continue
                    Message.objects.create(
                        streamer=streamer,
                        content=payload["message"],
                        sentiment=result["score"],
                        #label=result["label"],   # see Fix 4
                    )
                    print(
                        f"[{self.msg_count}] "
                        f"{payload['broadcaster_channel']}: "
                        f"{payload['message'][:60]} "
                        f"-> {result['label']} {result['score']:.3f}"
                    )

    def _drain_buffer(self, consumer: KafkaConsumer) -> list[dict]:
        """Pull up to BATCH_SIZE messages, but never block more than MAX_BATCH_WAIT_SECONDS."""
        buffer: list[dict] = []
        deadline = time.monotonic() + MAX_BATCH_WAIT_SECONDS
        while len(buffer) < BATCH_SIZE and time.monotonic() < deadline:
            payload = consumer.consume()
            if payload is not None:
                buffer.append(payload)
        return buffer


if __name__ == "__main__":
    Sentiment().run()

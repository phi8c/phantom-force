import asyncio
import json
import os

import aio_pika
from dotenv import load_dotenv


load_dotenv()


QUEUE_NAME = "download-queue"


async def main() -> None:
    rabbitmq_url = os.getenv("RABBITMQ_URL")

    if not rabbitmq_url:
        raise RuntimeError("RABBITMQ_URL is not configured")

    print("[1] Connecting...")

    connection = await aio_pika.connect_robust(rabbitmq_url)

    try:
        print("[2] Connected")

        channel = await connection.channel()

        queue = await channel.declare_queue(
            QUEUE_NAME,
            durable=True,
        )

        payload = {
            "ingestion_job_id": "rabbitmq-provider-test"
        }

        print("[3] Publishing:", payload)

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=QUEUE_NAME,
        )

        print("[4] Published")
        print("[5] Receiving...")

        message = await queue.get(
            timeout=10,
            fail=False,
        )

        if message is None:
            raise RuntimeError("No message received")

        received = json.loads(
            message.body.decode("utf-8")
        )

        print("[6] Received:", received)

        await message.ack()

        print("[7] ACK")
        print("[PASS] RabbitMQ test completed")

    finally:
        await connection.close()
        print("[8] Connection closed")


if __name__ == "__main__":
    asyncio.run(main())
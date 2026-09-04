import argparse
import asyncio

from azure.servicebus import ServiceBusSubQueue
from azure.servicebus.aio import ServiceBusClient

from shared.config.settings import settings


async def purge_receiver(receiver, label: str) -> int:
    deleted = 0

    while True:
        messages = await receiver.receive_messages(
            max_message_count=100,
            max_wait_time=2,
        )

        if not messages:
            break

        for message in messages:
            await receiver.complete_message(message)

        deleted += len(messages)
        print(f"{label}: deleted {deleted}")

    return deleted


async def purge_queue(queue_name: str) -> None:
    async with ServiceBusClient.from_connection_string(
        conn_str=settings.AZURE_SERVICE_BUS_CONNECTION_STRING,
    ) as client:

        # 1. Active messages
        async with client.get_queue_receiver(
            queue_name=queue_name,
            prefetch_count=100,
        ) as receiver:
            active_deleted = await purge_receiver(
                receiver,
                "Active",
            )

        # 2. Dead-letter messages
        async with client.get_queue_receiver(
            queue_name=queue_name,
            sub_queue=ServiceBusSubQueue.DEAD_LETTER,
            prefetch_count=100,
        ) as receiver:
            dead_deleted = await purge_receiver(
                receiver,
                "Dead letter",
            )

    print(
        f"Done '{queue_name}'. "
        f"Active={active_deleted}, "
        f"DeadLetter={dead_deleted}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue")

    args = parser.parse_args()

    asyncio.run(
        purge_queue(args.queue)
    )


if __name__ == "__main__":
    main()
import argparse
import asyncio

from azure.servicebus.aio import ServiceBusClient

from shared.config.settings import settings


async def purge_queue(queue_name: str) -> None:
    async with ServiceBusClient.from_connection_string(
        conn_str=settings.AZURE_SERVICE_BUS_CONNECTION_STRING,
    ) as client:

        async with client.get_queue_receiver(
            queue_name=queue_name,
            prefetch_count=100,
        ) as receiver:

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
                print(f"Deleted: {deleted}")

    print(f"Done. Deleted {deleted} messages from '{queue_name}'.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue")

    args = parser.parse_args()
    asyncio.run(purge_queue(args.queue))


if __name__ == "__main__":
    main()
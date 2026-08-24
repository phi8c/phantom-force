import asyncio

from app.workers.bootstrap.build_extract_consumer import (
    build_extract_consumer,
)


async def main():

    consumer = (
        build_extract_consumer()
    )

    print(
        "Extract Consumer Started"
    )

    await consumer.start()


if __name__ == "__main__":

    asyncio.run(
        main()
    )
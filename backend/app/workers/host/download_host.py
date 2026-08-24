import asyncio

from app.workers.bootstrap.build_download_consumer import (
    build_download_consumer,
)


async def main():

    consumer = (
        build_download_consumer()
    )

    print(
        "Download Consumer Started"
    )

    await consumer.start()


if __name__ == "__main__":

    asyncio.run(
        main()
    )
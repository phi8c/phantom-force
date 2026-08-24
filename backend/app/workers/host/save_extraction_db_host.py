import asyncio

from app.workers.bootstrap.build_save_extraction_consumer import (
    build_save_extraction_consumer,
)


async def main():

    consumer = (
        build_save_extraction_consumer()
    )

    await (
        consumer.start()
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
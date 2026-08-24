import asyncio

from app.workers.bootstrap.build_chunk_consumer import (
    build_chunk_consumer,
)


async def main():

    consumer = (
        build_chunk_consumer()
    )

    print(  
        "Chunk Consumer Started"
    )

    await (
        consumer.start()
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
import asyncio

from app.workers.bootstrap.build_extract_consumer import (
    build_extract_consumer,
)

from app.workers.bootstrap.build_save_extraction_consumer import (
    build_save_extraction_consumer,
)

from app.workers.bootstrap.build_save_extraction_storage_consumer import (
    build_save_extraction_storage_consumer,
)
from app.workers.bootstrap.build_chunk_consumer import (
    build_chunk_consumer,
)


async def main():

    extract_consumer = build_extract_consumer()

    save_db_consumer = (
        build_save_extraction_consumer()
    )

    save_storage_consumer = (
        build_save_extraction_storage_consumer()
    )
    
    chunk_consumer = (
    build_chunk_consumer()
)

    await asyncio.gather(
        extract_consumer.start(),
        save_db_consumer.start(),
        save_storage_consumer.start(),
        chunk_consumer.start(),
    )


if __name__ == "__main__":
    asyncio.run(main())
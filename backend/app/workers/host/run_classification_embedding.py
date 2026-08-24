import asyncio

from app.workers.bootstrap.build_classification_consumer import (
    build_classification_host,
)

from app.workers.bootstrap.build_embedding_consumer import (
    build_embedding_host,
)

import app.infrastructure.persistence.models


async def main():

    classification_host = (
        build_classification_host()
    )

    embedding_host = (
        build_embedding_host()
    )

    await asyncio.gather(
        classification_host.start(),
        embedding_host.start(),
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
    
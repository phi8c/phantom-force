class ChunkConfigurationResolver:

    def resolve(
        self,
        run,
    ) -> dict:

        configuration = (
            run.configuration
            or {}
        )

        return (
            configuration.get(
                "chunk",
                {}
            )
        )
from app.infrastructure.providers.datasource.sharepoint.sharepoint_service import (
    SharePointService,
)


class DiscoverSourcesUseCase:

    def __init__(
        self,
        sharepoint_service: SharePointService,
    ):
        self.sharepoint_service = (
            sharepoint_service
        )

    async def execute(
        self,
    ):

        result = []

        sites = await (
            self.sharepoint_service
            .get_sites()
        )

        for site in sites:

            enabled = await (
                self.sharepoint_service
                .is_rag_enabled(
                    site["id"],
                )
            )

            if not enabled:
                continue

            drives = await (
                self.sharepoint_service
                .get_drives(
                    site["id"],
                )
            )

            libraries = []

            for drive in drives.get(
                "value",
                [],
            ):

                folders = await (
                    self.sharepoint_service
                    .get_folder_tree(
                        drive["id"],
                    )
                )

                libraries.append(
                    {
                        "id": drive["id"],
                        "name": drive["name"],
                        "folders": folders,
                    }
                )

            result.append(
                {
                    "site_id": site["id"],
                    "site_name": site["name"],
                    "libraries": libraries,
                }
            )

        return result
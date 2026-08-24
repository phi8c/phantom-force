from app.domain.ports.datasource.sharepoint_gateway import (
    SharePointGateway,
)


class SharePointService:

    def __init__(
        self,
        gateway: SharePointGateway,
    ):
        self.gateway = gateway

    async def get_sites(
        self,
    ):
        return await (
            self.gateway.get_sites()
        )

    async def get_drives(
        self,
        site_id: str,
    ):
        return await (
            self.gateway.get_drives(
                site_id,
            )
        )

    async def get_folder_tree(
        self,
        drive_id: str,
    ):
        return await (
            self.gateway.get_folder_tree(
                drive_id,
            )
        )

    async def find_configuration_list(
        self,
        site_id: str,
    ):

        try:

            lists = await (
                self.gateway.get_lists(
                    site_id,
                )
            )

        except Exception:

            return None

        for item in lists.get(
            "value",
            [],
        ):

            if (
                item["displayName"]
                == "RAG Configuration"
            ):
                return item

        return None

    async def get_rag_configuration(
        self,
        site_id: str,
        list_id: str,
    ):
        return await (
            self.gateway.get_list_items(
                site_id,
                list_id,
            )
        )

    async def is_rag_enabled(
        self,
        site_id: str,
    ):

        configuration_list = (
            await self.find_configuration_list(
                site_id,
            )
        )

        if not configuration_list:
            return False

        configuration = await (
            self.get_rag_configuration(
                site_id,
                configuration_list["id"],
            )
        )

        items = configuration.get(
            "value",
            [],
        )

        if not items:
            return False

        fields = items[0]["fields"]

        return fields.get(
            "EnableRAG",
            False,
        )
    async def get_folder_children(
        self,
        drive_id: str,
        folder_id: str,
    ):
        return await (
            self.gateway.get_folder_children(
                drive_id,
                folder_id,
            )
        )
    
    async def get_drive_root_children(
        self,
        drive_id: str,
    ):
        return await (
            self.gateway.get_drive_root_children(
                drive_id,
            )
        )
    async def download_file(
        self,
        drive_id: str,
        file_id: str,
    ):
        return await (
            self.gateway.download_file(
                drive_id,
                file_id,
            )
        )
        
    async def get_file(
    self,
    drive_id: str,
    file_id: str,
):
        return await (
            self.gateway.get_file(
                drive_id,
                file_id,
            )
        )
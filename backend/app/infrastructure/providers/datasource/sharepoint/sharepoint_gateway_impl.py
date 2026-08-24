from app.domain.ports.datasource.sharepoint_gateway import (
    SharePointGateway,
)

from app.infrastructure.providers.datasource.sharepoint.graph_http_client import (
    GraphHttpClient,
)


class SharePointGatewayImpl(
    SharePointGateway,
):

    def __init__(
        self,
        graph_client: GraphHttpClient,
    ):
        self.graph_client = graph_client

    async def get_sites(
        self,
    ):

        response = await (
            self.graph_client.get(
                "/sites?search=*"
            )
        )

        return [
            {
                "id": site["id"],
                "name": site["displayName"],
            }
            for site in response.get(
                "value",
                [],
            )
        ]

    async def get_lists(
        self,
        site_id: str,
    ):

        return await (
            self.graph_client.get(
                f"/sites/{site_id}/lists"
                "?$select=id,displayName"
            )
        )

    async def get_list_items(
        self,
        site_id: str,
        list_id: str,
    ):

        return await (
            self.graph_client.get(
                f"/sites/{site_id}"
                f"/lists/{list_id}"
                "/items"
                "?expand=fields"
            )
        )

    async def get_drives(
        self,
        site_id: str,
    ):

        return await (
            self.graph_client.get(
                f"/sites/{site_id}/drives"
            )
        )

    async def get_folder_tree(
        self,
        drive_id: str,
    ):

        root_response = await (
            self.graph_client.get(
                f"/drives/{drive_id}"
                "/root/children"
            )
        )

        result = []

        for item in root_response.get(
            "value",
            [],
        ):

            if item.get(
                "folder"
            ):

                children = await (
                    self._load_children(
                        drive_id,
                        item["id"],
                    )
                )

                result.append(
                    {
                        "type": "FOLDER",
                        "id": item["id"],
                        "name": item["name"],
                        "children": children,
                    }
                )

                continue

            fields = await (
                self.get_file_metadata(
                    drive_id,
                    item["id"],
                )
            )

            result.append(
                {
                    "type": "FILE",
                    "id": item["id"],
                    "name": item["name"],
                    "size": item.get(
                        "size"
                    ),
                    "web_url": item.get(
                        "webUrl"
                    ),
                    "da_ingest": fields.get(
                        "DaIngest",
                        False,
                    ),
                }
            )

        return result
    async def _load_children(
        self,
        drive_id: str,
        item_id: str,
    ):

        response = await (
            self.graph_client.get(
                f"/drives/{drive_id}"
                f"/items/{item_id}"
                "/children"
            )
        )

        result = []

        for item in response.get(
            "value",
            [],
        ):

            if item.get(
                "folder"
            ):

                children = await (
                    self._load_children(
                        drive_id,
                        item["id"],
                    )
                )

                result.append(
                    {
                        "type": "FOLDER",
                        "id": item["id"],
                        "name": item["name"],
                        "children": children,
                    }
                )

                continue

            fields = await (
                self.get_file_metadata(
                    drive_id,
                    item["id"],
                )
            )

            result.append(
                {
                    "type": "FILE",
                    "id": item["id"],
                    "name": item["name"],
                    "size": item.get(
                        "size"
                    ),
                    "web_url": item.get(
                        "webUrl"
                    ),
                    "da_ingest": fields.get(
                        "DaIngest",
                        False,
                    ),
                }
            )

        return result
    
    async def get_file(
        self,
        drive_id: str,
        file_id: str,
    ):
        return await self.graph_client.get(
            f"/drives/{drive_id}/items/{file_id}"
        )
        
    async def get_folder_children(
        self,
        drive_id: str,
        folder_id: str,
    ):

        return await (
            self.graph_client.get(
                f"/drives/{drive_id}"
                f"/items/{folder_id}"
                "/children"
            )
        )
        
    async def get_drive_root_children(
        self,
        drive_id: str,
    ):

        return await (
            self.graph_client.get(
                f"/drives/{drive_id}"
                "/root/children"
            )
        )
        
    async def get_file_metadata(
        self,
        drive_id: str,
        item_id: str,
    ):

        try:

            response = await (
                self.graph_client.get(
                    f"/drives/{drive_id}"
                    f"/items/{item_id}"
                    "/listItem"
                    "?expand=fields"
                )
            )

            return response.get(
                "fields",
                {},
            )

        except Exception:
            return {}
        
    async def download_file(
        self,
        drive_id: str,
        file_id: str,
    ) -> bytes:

        return await (
            self.graph_client.download(
                f"/drives/{drive_id}"
                f"/items/{file_id}"
                "/content"
            )
        )
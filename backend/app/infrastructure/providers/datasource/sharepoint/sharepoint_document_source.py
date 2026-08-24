from app.domain.entities.discovered_file import DiscoveredFile
from app.domain.entities.ingestion_run import IngestionRun
from app.domain.ports.datasource.document_source import DocumentSource
from app.infrastructure.providers.datasource.sharepoint.sharepoint_service import SharePointService
from app.domain.enums.scope_type import ScopeType
from datetime import datetime

class SharePointDocumentSource(DocumentSource):

    def __init__(self, sharepoint_service: SharePointService):
        self.sharepoint_service = sharepoint_service

    async def discover_files(self, run: IngestionRun) -> list[DiscoveredFile]:
        if run.scope_type == ScopeType.FILE:
            return await self._discover_file(run)
        if run.scope_type == ScopeType.FOLDER:
            return await self._discover_folder(run)
        if run.scope_type == ScopeType.SITE:
            return await self._discover_site(run)
        if run.scope_type == ScopeType.SOURCE:
            return await self._discover_source(run)
        raise ValueError(f"Unsupported scope {run.scope_type}")

    async def _discover_folder(self, run: IngestionRun) -> list[DiscoveredFile]:
        result: list[DiscoveredFile] = []
        await self._load_folder_recursive(
            drive_id=run.scope_data["drive_id"],
            folder_id=run.scope_data["folder_id"],
            site_id=run.scope_data["site_id"],
            result=result,
        )
        return result

    async def _load_folder_recursive(self, drive_id: str, folder_id: str, site_id: str, result: list[DiscoveredFile]) -> None:
        response = await self.sharepoint_service.get_folder_children(drive_id, folder_id)
        for item in response.get("value", []):
            if item.get("folder"):
                await self._load_folder_recursive(drive_id=drive_id, folder_id=item["id"], site_id=site_id, result=result)
                continue
            
            result.append(DiscoveredFile(
                original_file_path=None,
                external_file_id=item["id"],
                file_name=item["name"],
                file_extension=item["name"].split(".")[-1] if "." in item["name"] else None,
                file_size_bytes=item.get("size"),
                source_file_url=item.get("webUrl"),
                provider_metadata={"site_id": site_id, "drive_id": drive_id, "folder_id": folder_id},
                last_modified_at=(
                datetime.fromisoformat(
                    item[
                        "lastModifiedDateTime"
                    ].replace(
                        "Z",
                        "+00:00",
                    )
                )
                if item.get(
                    "lastModifiedDateTime"
                )
                else None
            ),
            ))

    async def _discover_file(self, run: IngestionRun) -> list[DiscoveredFile]:
        file = await self.sharepoint_service.get_file(drive_id=run.scope_data["drive_id"], file_id=run.scope_data["file_id"])
        return [DiscoveredFile(
            original_file_path=None,
            external_file_id=file["id"],
            file_name=file["name"],
            file_extension=file["name"].split(".")[-1] if "." in file["name"] else None,
            file_size_bytes=file.get("size"),
            source_file_url=file.get("webUrl"),
            provider_metadata={
                "site_id": run.scope_data["site_id"],
                "drive_id": run.scope_data["drive_id"],
                "folder_id": run.scope_data.get("folder_id"),
            },
            last_modified_at=file.get("lastModifiedDateTime"),
        )]

    async def _discover_site(self, run: IngestionRun) -> list[DiscoveredFile]:
        result: list[DiscoveredFile] = []
        site_id = run.scope_data["site_id"]
        drives_response = await self.sharepoint_service.get_drives(site_id)
        
        for drive in drives_response.get("value", []):
            drive_id = drive["id"]
            root_response = await self.sharepoint_service.get_drive_root_children(drive_id)
            for item in root_response.get("value", []):
                if item.get("folder"):
                    await self._load_folder_recursive(drive_id=drive_id, folder_id=item["id"], site_id=site_id, result=result)
                    continue
                
                result.append(DiscoveredFile(
                    original_file_path=None,
                    external_file_id=item["id"],
                    file_name=item["name"],
                    file_extension=item["name"].split(".")[-1] if "." in item["name"] else None,
                    file_size_bytes=item.get("size"),
                    source_file_url=item.get("webUrl"),
                    provider_metadata={"site_id": site_id, "drive_id": drive_id, "folder_id": None},
                    last_modified_at=item.get("lastModifiedDateTime"),
                ))
        return result

    async def _discover_source(self, run: IngestionRun) -> list[DiscoveredFile]:
        result: list[DiscoveredFile] = []
        sites = await self.sharepoint_service.get_sites()
        
        for site in sites:
            site_id = site["id"]
            drives_response = await self.sharepoint_service.get_drives(site_id)
            for drive in drives_response.get("value", []):
                drive_id = drive["id"]
                root_response = await self.sharepoint_service.get_drive_root_children(drive_id)
                for item in root_response.get("value", []):
                    if item.get("folder"):
                        await self._load_folder_recursive(drive_id=drive_id, folder_id=item["id"], site_id=site_id, result=result)
                        continue
                    
                    result.append(DiscoveredFile(
                        original_file_path=None,
                        external_file_id=item["id"],
                        file_name=item["name"],
                        file_extension=item["name"].split(".")[-1] if "." in item["name"] else None,
                        file_size_bytes=item.get("size"),
                        source_file_url=item.get("webUrl"),
                        provider_metadata={"site_id": site_id, "drive_id": drive_id, "folder_id": None},
                        last_modified_at=item.get("lastModifiedDateTime"),
                    ))
        return result

    async def download_file(self, **kwargs):
        raise NotImplementedError()
    
    async def download_file(
        self,
        provider_metadata: dict,
        external_file_id: str,
    ) -> bytes:

        return await self.sharepoint_service.download_file(
            drive_id=provider_metadata["drive_id"],
            file_id=external_file_id,
        )
from uuid import UUID

from module.ingest.config.application.dtos.ingestion_job_scope import (
    IngestionJobScopeResponse,
    SaveIngestionJobScopeCommand,
)
from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.contracts.unit_of_work import (
    UnitOfWork,
)


class SaveIngestionJobScopeUseCase:

    def __init__(
        self,
        *,
        ingestion_config_repository: IngestionConfigRepository,
        uow: UnitOfWork,
    ):
        self.ingestion_config_repository = (
            ingestion_config_repository
        )
        self.uow = uow

    async def execute(
        self,
        command: SaveIngestionJobScopeCommand,
    ) -> IngestionJobScopeResponse:

        job = await self.ingestion_config_repository.get_job_by_id(
            command.ingestion_job_id,
        )

        if job is None:
            raise LookupError(
                "ingestion_job_id was not found"
            )

        scope_type = command.scope_type.strip().upper()

        if not scope_type:
            raise ValueError(
                "scope_type must not be empty"
            )

        scope_data = self._validate_scope_data(
            scope_type=scope_type,
            scope_data=command.scope_data,
        )

        try:
            job = await (
                self.ingestion_config_repository
                .update_job_scope(
                    job_id=command.ingestion_job_id,
                    scope_type=scope_type,
                    scope_data=scope_data,
                )
            )

            await self.uow.commit()

        except Exception:
            await self.uow.rollback()
            raise

        return IngestionJobScopeResponse(
            ingestion_job_id=job.id or command.ingestion_job_id,
            scope_type=job.scope_type,
            scope_data=job.scope_data,
        )

    def _validate_scope_data(
        self,
        *,
        scope_type: str,
        scope_data: dict,
    ) -> dict:

        if not isinstance(scope_data, dict):
            raise ValueError(
                "scope_data must be an object"
            )

        if scope_type != "SELECTED_ROOTS":
            if not scope_data:
                raise ValueError(
                    "scope_data must not be empty"
                )

            return scope_data

        roots = scope_data.get("roots")

        if not isinstance(roots, list) or not roots:
            raise ValueError(
                "scope_data.roots must be a non-empty list"
            )

        normalized_roots = []
        seen_roots = set()
        selected_drive_roots = set()

        for root in roots:
            if not isinstance(root, dict):
                raise ValueError(
                    "scope_data.roots items must be objects"
                )

            site_id = self._require_non_empty_string(
                root.get("site_id"),
                "site_id",
            )
            drive_id = self._require_non_empty_string(
                root.get("drive_id"),
                "drive_id",
            )
            folder_id = root.get("folder_id")

            if folder_id is not None:
                folder_id = self._require_non_empty_string(
                    folder_id,
                    "folder_id",
                )

            root_key = (
                site_id,
                drive_id,
                folder_id,
            )
            drive_key = (
                site_id,
                drive_id,
            )

            if root_key in seen_roots:
                raise ValueError(
                    "scope_data.roots contains duplicate roots"
                )

            if folder_id is None:
                if drive_key in selected_drive_roots:
                    raise ValueError(
                        "scope_data.roots contains duplicate drive roots"
                    )

                selected_drive_roots.add(
                    drive_key,
                )
            elif drive_key in selected_drive_roots:
                raise ValueError(
                    "scope_data.roots contains overlapping roots"
                )

            seen_roots.add(
                root_key,
            )
            normalized_roots.append(
                {
                    "site_id": site_id,
                    "drive_id": drive_id,
                    "folder_id": folder_id,
                }
            )

        for site_id, drive_id, folder_id in seen_roots:
            if folder_id is None:
                continue

            if (
                site_id,
                drive_id,
            ) in selected_drive_roots:
                raise ValueError(
                    "scope_data.roots contains overlapping roots"
                )

        return {
            **scope_data,
            "roots": normalized_roots,
        }

    @staticmethod
    def _require_non_empty_string(
        value,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

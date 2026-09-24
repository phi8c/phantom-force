from __future__ import annotations

import unittest

from module.ingest.config.application.use_cases.save_ingestion_job_scope import (
    SaveIngestionJobScopeUseCase,
)


class ScopeCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.use_case = SaveIngestionJobScopeUseCase(
            ingestion_config_repository=object(),
            uow=object(),
        )

    def test_accepts_provider_neutral_locator_roots(self) -> None:
        scope = self.use_case._validate_scope_data(
            scope_type="SELECTED_ROOTS",
            scope_data={"roots": [{"locator": {"path": "/folder"}}]},
        )

        self.assertEqual(
            scope,
            {"roots": [{"locator": {"path": "/folder"}}]},
        )

    def test_keeps_legacy_sharepoint_roots_compatible(self) -> None:
        scope = self.use_case._validate_scope_data(
            scope_type="SELECTED_ROOTS",
            scope_data={
                "roots": [
                    {"site_id": "site", "drive_id": "drive", "folder_id": "folder"}
                ]
            },
        )

        self.assertEqual(scope["roots"][0]["site_id"], "site")
        self.assertEqual(scope["roots"][0]["folder_id"], "folder")


if __name__ == "__main__":
    unittest.main()

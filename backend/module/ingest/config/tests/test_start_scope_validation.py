from __future__ import annotations

import unittest

from module.ingest.config.application.use_cases.start_existing_ingestion_job import (
    StartExistingIngestionJobUseCase,
)


class StartScopeValidationTests(unittest.TestCase):
    def test_accepts_multiple_generic_roots(self) -> None:
        StartExistingIngestionJobUseCase._validate_scope(
            scope_type="SELECTED_ROOTS",
            scope_data={
                "roots": [
                    {"locator": {"path": "/A"}},
                    {"locator": {"opaque": "value"}},
                ]
            },
        )

    def test_accepts_legacy_sharepoint_roots(self) -> None:
        StartExistingIngestionJobUseCase._validate_scope(
            scope_type="SELECTED_ROOTS",
            scope_data={
                "roots": [
                    {"site_id": "site", "drive_id": "drive", "folder_id": None}
                ]
            },
        )

    def test_rejects_empty_generic_locator(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty object"):
            StartExistingIngestionJobUseCase._validate_scope(
                scope_type="SELECTED_ROOTS",
                scope_data={"roots": [{"locator": {}}]},
            )

    def test_rejects_mixed_scope_formats(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot mix"):
            StartExistingIngestionJobUseCase._validate_scope(
                scope_type="SELECTED_ROOTS",
                scope_data={
                    "roots": [
                        {"locator": {"path": "/A"}},
                        {"site_id": "site", "drive_id": "drive"},
                    ]
                },
            )


if __name__ == "__main__":
    unittest.main()

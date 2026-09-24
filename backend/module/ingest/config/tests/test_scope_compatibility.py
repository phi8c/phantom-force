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

    def test_accepts_multiple_provider_neutral_locator_roots(self) -> None:
        scope = self.use_case._validate_scope_data(
            scope_type="SELECTED_ROOTS",
            scope_data={
                "roots": [
                    {"locator": {"opaque": "first"}},
                    {"locator": {"anything": {"nested": True}}},
                ]
            },
        )

        self.assertEqual(
            scope,
            {
                "roots": [
                    {"locator": {"opaque": "first"}},
                    {"locator": {"anything": {"nested": True}}},
                ]
            },
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

    def test_rejects_mixed_generic_and_legacy_roots(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot mix"):
            self.use_case._validate_scope_data(
                scope_type="SELECTED_ROOTS",
                scope_data={
                    "roots": [
                        {"locator": {"opaque": "value"}},
                        {"site_id": "site", "drive_id": "drive"},
                    ]
                },
            )

    def test_rejects_empty_generic_locator(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty object"):
            self.use_case._validate_scope_data(
                scope_type="SELECTED_ROOTS",
                scope_data={"roots": [{"locator": {}}]},
            )


if __name__ == "__main__":
    unittest.main()

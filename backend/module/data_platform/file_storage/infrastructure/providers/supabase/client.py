from supabase import Client
from supabase import create_client


class SupabaseClientFactory:

    @staticmethod
    def create(
        url: str,
        key: str,
    ) -> Client:
        return create_client(
            url,
            key,
        )
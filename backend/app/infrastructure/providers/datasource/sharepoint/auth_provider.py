from azure.identity import ClientSecretCredential

from app.shared.config.settings import (
    settings,
)


class AuthProvider:

    @staticmethod
    def get_credential():   

        return ClientSecretCredential(
            tenant_id=settings.GRAPH_TENANT_ID,
            client_id=settings.GRAPH_CLIENT_ID,
            client_secret=settings.GRAPH_CLIENT_SECRET,
        )
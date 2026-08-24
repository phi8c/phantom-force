from pydantic import BaseModel


class DownloadTaskMessage(
    BaseModel,
):
    task_id: str

    document_id: str

    task_type: str
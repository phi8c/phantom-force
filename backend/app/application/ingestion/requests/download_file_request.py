from pydantic import BaseModel


class DownloadFileRequest(
    BaseModel,
):
    drive_id: str

    file_id: str
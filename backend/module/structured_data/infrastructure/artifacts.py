import asyncio
from pathlib import PurePosixPath

from .workbook import checksum


class FileStorageArtifacts:
    def __init__(self, file_storage=None, uploader=None, *, max_download_bytes=512*1024*1024):
        self.storage = file_storage
        self.uploader = uploader
        self.max_bytes = max_download_bytes

    @staticmethod
    def validate_path(path):
        if not isinstance(path,str) or not path.startswith('structured/') or '..' in PurePosixPath(path).parts or '\\' in path or ':' in path:
            raise ValueError('Invalid structured artifact path')

    async def upload(self, path, source, content_type):
        self.validate_path(path)
        async def content():
            with source.open('rb') as stream:
                while chunk := stream.read(64*1024):
                    yield chunk
                    await asyncio.sleep(0)
        stored = await self.uploader.upload_stream(path=path, content=content(), content_type=content_type)
        if stored.path != path:
            raise ValueError('Structured artifact upload path mismatch')

    async def download(self, path, destination, expected_checksum):
        self.validate_path(path)
        stream_method = getattr(self.storage, 'download_stream', None)
        async def content():
            if stream_method:
                async for chunk in stream_method(path=path):
                    yield chunk
            else:
                yield await self.storage.download(path)
        try:
            size = 0
            with destination.open('wb') as target:
                async for chunk in content():
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise ValueError('Parquet artifact exceeds the query download budget')
                    target.write(chunk)
            if await asyncio.to_thread(checksum, destination) != expected_checksum:
                raise ValueError('Parquet checksum mismatch; rebuild the dataset')
        except BaseException:
            destination.unlink(missing_ok=True)
            raise

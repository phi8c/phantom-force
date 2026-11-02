"""Bounded local cache of immutable, checksum-pinned Parquet artifacts."""
import hashlib
import os
from pathlib import Path
import shutil
from uuid import uuid4

from module.structured_data.application.services import blocking
from .artifacts import FileStorageArtifacts
from .workbook import checksum


class CachedArtifacts:
    def __init__(self, delegate, root, *, max_bytes=5*1024*1024*1024):
        self.delegate, self.root, self.max_bytes = delegate, Path(root), max_bytes

    async def upload(self, path, source, content_type):
        await self.delegate.upload(path,source,content_type)

    async def download(self, path, destination, expected_checksum):
        FileStorageArtifacts.validate_path(path)
        self.root.mkdir(parents=True,exist_ok=True)
        identity = hashlib.sha256((path+'\n'+expected_checksum).encode()).hexdigest()
        cached = self.root/(identity+'.parquet')
        def copy_cached():
            try:
                if cached.is_file() and checksum(cached) == expected_checksum:
                    shutil.copyfile(cached,destination)
                    os.utime(cached,None)
                    return True
            except OSError:
                pass
            return False
        if await blocking(copy_cached):
            return
        temporary = self.root/(identity+'.'+str(uuid4())+'.tmp')
        try:
            await self.delegate.download(path,temporary,expected_checksum)
            def publish():
                if checksum(temporary) != expected_checksum:
                    raise ValueError('Cache publication checksum mismatch')
                if temporary.stat().st_size > self.max_bytes:
                    shutil.copyfile(temporary,destination)
                    temporary.unlink()
                    return
                shutil.copyfile(temporary,destination)
                os.replace(temporary,cached)
                files = []
                for item in self.root.glob('*.parquet'):
                    try:
                        info = item.stat()
                        files.append((info.st_mtime,item,info.st_size))
                    except OSError:
                        pass
                files.sort(key=lambda value:value[0])
                total = sum(value[2] for value in files)
                for _,item,size in files:
                    if total <= self.max_bytes:
                        break
                    if item == cached:
                        continue
                    try:
                        item.unlink()
                        total -= size
                    except OSError:
                        pass
            await blocking(publish)
        finally:
            temporary.unlink(missing_ok=True)

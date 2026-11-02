from functools import lru_cache


@lru_cache(maxsize=1)
def structured_file_storage():
    from module.data_platform.file_storage.composition import create_supabase_file_storage
    from shared.config.settings import settings
    return create_supabase_file_storage(url=settings.SUPABASE_URL,key=settings.SUPABASE_KEY,
                                        bucket=settings.SUPABASE_STORAGE_BUCKET)


def create_chat_structured_reader(*, session, gateway, prompt_provider):
    from module.structured_data.composition import create_structured_reader
    class LazyStorage:
        async def download(self, path):
            return await structured_file_storage().download(path)
    return create_structured_reader(session=session,file_storage=LazyStorage(),
                                     gateway=gateway,prompt_provider=prompt_provider)

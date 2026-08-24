from abc import ABC
from abc import abstractmethod


class SharePointGateway(
    ABC,
):

    @abstractmethod
    async def get_sites(
        self,
    ):
        pass

    @abstractmethod
    async def get_lists(
        self,
        site_id: str,
    ):
        pass

    @abstractmethod
    async def get_list_items(
        self,
        site_id: str,
        list_id: str,
    ):
        pass

    @abstractmethod
    async def get_drives(
        self,
        site_id: str,
    ):
        pass


    
    @abstractmethod
    async def get_folder_tree(
        self,
        drive_id: str,
    ):
        pass
    
    @abstractmethod
    async def get_file(
        self,
        drive_id: str,
        file_id: str,
    ):
        pass


    @abstractmethod
    async def get_folder_children(
        self,
        drive_id: str,
        folder_id: str,
    ):
        pass


    @abstractmethod
    async def get_drive_root_children(
        self,
        drive_id: str,
    ):
        pass
    
    @abstractmethod
    async def download_file(
        self,
        drive_id: str,
        file_id: str,
    ) -> bytes:
        pass
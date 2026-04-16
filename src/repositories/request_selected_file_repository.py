from src.models.request_selected_files import RequestSelectedFile
from src.repositories.base import BaseRepository


class RequestSelectedFileRepository(BaseRepository[RequestSelectedFile]):
    model_class = RequestSelectedFile

    def get_by_request_message_id(
        self, request_message_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[RequestSelectedFile], int]:
        """Lấy danh sách selected file theo request_message_id với phân trang"""
        return self.get_all(
            skip=skip, limit=limit, request_message_id=request_message_id
        )

    def get_by_file_id(
        self, file_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[RequestSelectedFile], int]:
        """Lấy danh sách selected file theo file_id với phân trang"""
        return self.get_all(skip=skip, limit=limit, file_id=file_id)

    def get_by_request_and_file(
        self, request_message_id: int, file_id: int
    ) -> RequestSelectedFile | None:
        """Lấy selected file theo request_message_id và file_id"""
        return self.get_one(request_message_id=request_message_id, file_id=file_id)

    def get_files_for_request(
        self, request_message_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[RequestSelectedFile], int]:
        """Lấy danh sách file được chọn cho request message"""
        return self.get_by_request_message_id(request_message_id, skip, limit)

    def get_requests_for_file(
        self, file_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[RequestSelectedFile], int]:
        """Lấy danh sách request message sử dụng file"""
        return self.get_by_file_id(file_id, skip, limit)

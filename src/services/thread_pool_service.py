import atexit
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional

logger = logging.getLogger(__name__)


class ThreadPoolService:
    """Service quản lý thread pool cho xử lý song song.

    Sử dụng concurrent.futures.ThreadPoolExecutor để chạy các tác vụ
    không phụ thuộc lẫn nhau song song, giảm thời gian xử lý tổng thể.

    Cách dùng:
        pool = ThreadPoolService(max_workers=4)
        results = pool.run_parallel([task1, task2, task3])
        # results[i] là kết quả hoặc Exception nếu task thất bại
    """

    def __init__(self, max_workers: int = 4, name: str = "default"):
        self.max_workers = max_workers
        self.name = name
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=f"ThreadPool-{name}",
        )
        logger.info(
            "ThreadPoolService '%s' initialized with %d workers", name, max_workers
        )

    def run_parallel(self, tasks: List[Callable[[], Any]]) -> List[Any]:
        """Chạy nhiều tác vụ song song.

        Args:
            tasks: Danh sách các callable không tham số.

        Returns:
            List kết quả theo đúng thứ tự tasks.
            Nếu task thất bại, phần tử tương ứng là Exception.
        """
        if not tasks:
            return []

        future_to_idx = {
            self._executor.submit(task): i for i, task in enumerate(tasks)
        }
        results: List[Any] = [None] * len(tasks)

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logger.error(
                    "Task #%d in pool '%s' failed: %s",
                    idx,
                    self.name,
                    e,
                    exc_info=True,
                )
                results[idx] = e

        return results

    def shutdown(self, wait: bool = True):
        """Giải phóng thread pool."""
        self._executor.shutdown(wait=wait)
        logger.info("ThreadPoolService '%s' shut down", self.name)


# Singleton toàn cục — dùng chung cho toàn bộ ứng dụng
_global_pool: Optional[ThreadPoolService] = None


def get_thread_pool(max_workers: int = None) -> ThreadPoolService:
    """Lấy hoặc tạo ThreadPoolService singleton.

    Dùng chung một pool xuyên suốt vòng đời ứng dụng,
    tránh tạo thread mới cho mỗi request.
    """
    global _global_pool
    if _global_pool is None:
        _global_pool = ThreadPoolService(
            max_workers=max_workers or 4,
            name="global",
        )
        atexit.register(_global_pool.shutdown)
    return _global_pool

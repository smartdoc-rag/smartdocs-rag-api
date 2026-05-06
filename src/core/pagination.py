from dataclasses import dataclass


@dataclass
class PaginationParams:
    page: int
    page_size: int

    @classmethod
    def from_request(cls, request, default_page=1, default_page_size=20, max_page_size=100):
        page = int(request.GET.get("page", default_page))
        page_size = int(request.GET.get("page_size", default_page_size))
        page_size = min(page_size, max_page_size)
        return cls(page=page, page_size=page_size)

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def build_pagination_meta(page: int, page_size: int, total: int) -> dict:
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "current_page": page,
        "page_size": page_size,
        "total_items": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "next_page": page + 1 if page < total_pages else None,
        "previous_page": page - 1 if page > 1 else None,
    }


@dataclass
class CursorPaginationParams:
    cursor: str | None
    limit: int

    @classmethod
    def from_request(cls, request, default_limit=20, max_limit=100):
        cursor = request.GET.get("cursor")
        limit = int(request.GET.get("limit", default_limit))
        limit = min(limit, max_limit)
        return cls(cursor=cursor, limit=limit)
    



def build_cursor_pagination_meta(next_cursor: str | None, has_next: bool) -> dict:
    return {
        "next_cursor": next_cursor,
        "has_next": has_next,
    }
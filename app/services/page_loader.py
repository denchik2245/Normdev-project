from dataclasses import dataclass
import time

import httpx


@dataclass
class PageLoadResult:
    url: str
    final_url: str
    status_code: int
    response_time_ms: float
    html: str
    headers: dict[str, str]
    is_https: bool


class PageLoaderError(Exception):
    pass


class PageLoader:
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    def load(self, url: str) -> PageLoadResult:
        start_time = time.perf_counter()

        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "SiteAuditBot/1.0 "
                        "(Educational project for website technical audit)"
                    )
                },
            ) as client:
                response = client.get(url)

            end_time = time.perf_counter()
            response_time_ms = round((end_time - start_time) * 1000, 2)

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type.lower():
                raise PageLoaderError(
                    "Указанный адрес не вернул HTML-страницу."
                )

            return PageLoadResult(
                url=url,
                final_url=str(response.url),
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                html=response.text,
                headers=dict(response.headers),
                is_https=str(response.url).startswith("https://"),
            )

        except httpx.TimeoutException as exc:
            raise PageLoaderError(
                "Сайт не ответил вовремя. Превышено время ожидания."
            ) from exc
        except httpx.RequestError as exc:
            raise PageLoaderError(
                "Не удалось подключиться к сайту. Проверьте URL и доступность ресурса."
            ) from exc
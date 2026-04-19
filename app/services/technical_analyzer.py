from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class TechnicalIssueData:
    severity: str
    title: str
    description: str
    recommendation: str


@dataclass
class TechnicalAnalysisResult:
    metrics: list[tuple[str, float, str | None]]
    issues: list[TechnicalIssueData]


class TechnicalAnalyzer:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def analyze(
        self,
        original_url: str,
        final_url: str,
        html: str,
        status_code: int,
        headers: dict[str, str],
        is_https: bool,
    ) -> TechnicalAnalysisResult:
        issues: list[TechnicalIssueData] = []
        metrics: list[tuple[str, float, str | None]] = []

        parsed_final = urlparse(final_url)
        base_url = f"{parsed_final.scheme}://{parsed_final.netloc}"

        metrics.append(("uses_https", 1.0 if is_https else 0.0, None))
        if not is_https:
            issues.append(
                TechnicalIssueData(
                    severity="high",
                    title="Сайт не использует HTTPS",
                    description="Финальный адрес страницы работает не по HTTPS.",
                    recommendation="Настроить SSL-сертификат и перенаправление всех HTTP-запросов на HTTPS."
                )
            )

        redirected = self._normalize_url(original_url) != self._normalize_url(final_url)
        metrics.append(("has_redirect", 1.0 if redirected else 0.0, None))
        if redirected:
            issues.append(
                TechnicalIssueData(
                    severity="low",
                    title="Обнаружен редирект",
                    description=f"Запрошенный URL был перенаправлен на {final_url}.",
                    recommendation="Проверить, что редирект корректен и не создает лишних переходов."
                )
            )

        metrics.append(("main_status_code", float(status_code), None))
        if status_code >= 400:
            issues.append(
                TechnicalIssueData(
                    severity="high",
                    title="Страница возвращает ошибку",
                    description=f"Основная страница вернула HTTP-статус {status_code}.",
                    recommendation="Исправить ошибку ответа сервера и обеспечить доступность страницы."
                )
            )

        robots_ok = self._check_common_file(urljoin(base_url, "/robots.txt"))
        sitemap_ok = self._check_common_file(urljoin(base_url, "/sitemap.xml"))

        metrics.append(("robots_txt_available", 1.0 if robots_ok else 0.0, None))
        metrics.append(("sitemap_xml_available", 1.0 if sitemap_ok else 0.0, None))

        if not robots_ok:
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="Файл robots.txt недоступен",
                    description="Не удалось получить корректный ответ от robots.txt.",
                    recommendation="Добавить и настроить robots.txt в корне сайта."
                )
            )

        if not sitemap_ok:
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="Файл sitemap.xml недоступен",
                    description="Не удалось получить корректный ответ от sitemap.xml.",
                    recommendation="Сгенерировать sitemap.xml и разместить его в корне сайта."
                )
            )

        links_total, broken_links = self._check_links(html, base_url)

        metrics.append(("links_count", float(links_total), None))
        metrics.append(("broken_links_count", float(broken_links), None))

        if broken_links > 0:
            severity = "high" if broken_links >= 3 else "medium"
            issues.append(
                TechnicalIssueData(
                    severity=severity,
                    title="Обнаружены битые ссылки",
                    description=f"Найдено {broken_links} битых ссылок из {links_total} проверенных.",
                    recommendation="Исправить или удалить неработающие ссылки."
                )
            )

        server_header = headers.get("server", "")
        metrics.append(("has_server_header", 1.0 if server_header else 0.0, None))

        return TechnicalAnalysisResult(metrics=metrics, issues=issues)

    def _check_common_file(self, url: str) -> bool:
        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "SiteAuditBot/1.0"},
            ) as client:
                response = client.get(url)
                return response.status_code < 400
        except httpx.RequestError:
            return False

    def _check_links(self, html: str, base_url: str) -> tuple[int, int]:
        soup = BeautifulSoup(html, "html.parser")
        hrefs: list[str] = []

        for a_tag in soup.find_all("a", href=True):
            href = (a_tag.get("href") or "").strip()
            if not href:
                continue
            if href.startswith("#"):
                continue
            if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
                continue
            hrefs.append(urljoin(base_url, href))

        unique_hrefs = list(dict.fromkeys(hrefs))
        total_links = len(unique_hrefs)

        broken_links = 0
        for link in unique_hrefs[:20]:
            if not self._is_link_ok(link):
                broken_links += 1

        return total_links, broken_links

    def _is_link_ok(self, url: str) -> bool:
        try:
            with httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "SiteAuditBot/1.0"},
            ) as client:
                response = client.head(url)

                if response.status_code >= 400 or response.status_code == 405:
                    response = client.get(url)

                return response.status_code < 400
        except httpx.RequestError:
            return False

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{path}"
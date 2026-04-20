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
        soup = BeautifulSoup(html, "html.parser")
        response_headers = {key.lower(): value for key, value in headers.items()}
        final_hostname = parsed_final.hostname or ""

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

        content_type = response_headers.get("content-type", "")
        has_html_content_type = "text/html" in content_type.lower()
        has_charset = "charset=" in content_type.lower()
        metrics.append(("has_html_content_type", 1.0 if has_html_content_type else 0.0, None))
        metrics.append(("has_charset_in_content_type", 1.0 if has_charset else 0.0, None))

        if content_type and not has_html_content_type:
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="Неожиданный Content-Type",
                    description=f"Основная страница отдает заголовок Content-Type: {content_type}.",
                    recommendation="Проверить, что HTML-страницы возвращаются с типом text/html и корректной кодировкой."
                )
            )
        elif not content_type:
            issues.append(
                TechnicalIssueData(
                    severity="low",
                    title="Отсутствует Content-Type",
                    description="Основная страница не вернула заголовок Content-Type.",
                    recommendation="Добавить корректный заголовок Content-Type с указанием text/html и charset."
                )
            )

        if has_html_content_type and not has_charset:
            issues.append(
                TechnicalIssueData(
                    severity="low",
                    title="Не указана кодировка страницы",
                    description="В заголовке Content-Type отсутствует charset для HTML-страницы.",
                    recommendation="Добавить charset в заголовок Content-Type, например UTF-8."
                )
            )

        viewport_present = self._has_viewport_meta(soup)
        metrics.append(("has_viewport_meta", 1.0 if viewport_present else 0.0, None))
        if not viewport_present:
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="Отсутствует viewport meta tag",
                    description="На странице не найден meta viewport, что может ухудшать отображение на мобильных устройствах.",
                    recommendation='Добавить тег `<meta name="viewport" content="width=device-width, initial-scale=1">`.'
                )
            )

        compression_enabled = self._has_compression_header(response_headers)
        metrics.append(("has_compression", 1.0 if compression_enabled else 0.0, None))
        if not compression_enabled:
            issues.append(
                TechnicalIssueData(
                    severity="low",
                    title="Сжатие ответа не обнаружено",
                    description="В ответе не найдены признаки gzip, br или deflate-сжатия.",
                    recommendation="Включить HTTP-сжатие для HTML-страниц, чтобы ускорить загрузку."
                )
            )

        cache_control = response_headers.get("cache-control", "")
        has_cache_control = bool(cache_control)
        cacheable_html = self._is_html_cacheable(cache_control)
        metrics.append(("has_cache_control", 1.0 if has_cache_control else 0.0, None))
        metrics.append(("html_cacheable", 1.0 if cacheable_html else 0.0, None))
        if not has_cache_control:
            issues.append(
                TechnicalIssueData(
                    severity="low",
                    title="Отсутствует Cache-Control",
                    description="Для основной HTML-страницы не задан заголовок Cache-Control.",
                    recommendation="Настроить стратегию кэширования HTML-ответов с учетом обновляемости контента."
                )
            )

        hsts_header = response_headers.get("strict-transport-security", "")
        has_hsts = bool(hsts_header)
        metrics.append(("has_hsts", 1.0 if has_hsts else 0.0, None))
        if is_https and not has_hsts:
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="Не настроен HSTS",
                    description="Сайт работает по HTTPS, но не возвращает Strict-Transport-Security.",
                    recommendation="Добавить HSTS-заголовок после проверки корректной HTTPS-конфигурации."
                )
            )

        security_headers = {
            "x-content-type-options": "has_x_content_type_options",
            "x-frame-options": "has_x_frame_options",
            "content-security-policy": "has_content_security_policy",
            "referrer-policy": "has_referrer_policy",
            "permissions-policy": "has_permissions_policy",
        }
        missing_security_headers: list[str] = []
        for header_name, metric_name in security_headers.items():
            present = bool(response_headers.get(header_name))
            metrics.append((metric_name, 1.0 if present else 0.0, None))
            if not present:
                missing_security_headers.append(header_name)

        if missing_security_headers:
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="Отсутствуют базовые security headers",
                    description=(
                        "Не найдены некоторые защитные заголовки: "
                        + ", ".join(missing_security_headers) + "."
                    ),
                    recommendation="Добавить базовые security headers на уровне веб-сервера или приложения."
                )
            )

        x_robots_tag = response_headers.get("x-robots-tag", "")
        has_x_robots_tag = bool(x_robots_tag)
        metrics.append(("has_x_robots_tag", 1.0 if has_x_robots_tag else 0.0, None))
        metrics.append((
            "x_robots_tag_blocks_indexing",
            1.0 if self._robots_directives_block_indexing(x_robots_tag) else 0.0,
            None,
        ))
        if self._robots_directives_block_indexing(x_robots_tag):
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="X-Robots-Tag блокирует индексацию",
                    description=f"Заголовок X-Robots-Tag содержит ограничивающие директивы: {x_robots_tag}.",
                    recommendation="Проверить, что запрет индексации задан осознанно только для нужных страниц."
                )
            )

        www_consistent = self._check_www_consistency(final_url)
        metrics.append(("www_host_consistent", 1.0 if www_consistent else 0.0, None))
        if not www_consistent:
            issues.append(
                TechnicalIssueData(
                    severity="low",
                    title="Возможна несогласованность www/non-www",
                    description="Альтернативная версия домена www или без www отвечает отдельно без явной канонизации.",
                    recommendation="Настроить единый канонический хост и постоянный редирект между www и non-www версиями."
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

        link_stats = self._check_links(html, base_url)

        metrics.append(("links_count", float(link_stats["links_count"]), None))
        metrics.append(("broken_links_count", float(link_stats["broken_links_count"]), None))
        metrics.append(("technical_internal_links_count", float(link_stats["internal_links_count"]), None))
        metrics.append(("technical_external_links_count", float(link_stats["external_links_count"]), None))
        metrics.append(("broken_internal_links_count", float(link_stats["broken_internal_links_count"]), None))
        metrics.append(("broken_external_links_count", float(link_stats["broken_external_links_count"]), None))
        metrics.append(("mailto_links_count", float(link_stats["mailto_links_count"]), None))
        metrics.append(("tel_links_count", float(link_stats["tel_links_count"]), None))
        metrics.append(("mixed_content_count", float(link_stats["mixed_content_count"]), None))

        if link_stats["broken_links_count"] > 0:
            severity = "high" if link_stats["broken_links_count"] >= 3 else "medium"
            issues.append(
                TechnicalIssueData(
                    severity=severity,
                    title="Обнаружены битые ссылки",
                    description=(
                        f"Найдено {link_stats['broken_links_count']} битых ссылок "
                        f"из {link_stats['links_count']} проверенных "
                        f"(внутренних: {link_stats['broken_internal_links_count']}, "
                        f"внешних: {link_stats['broken_external_links_count']})."
                    ),
                    recommendation="Исправить или удалить неработающие ссылки."
                )
            )

        if link_stats["mixed_content_count"] > 0:
            issues.append(
                TechnicalIssueData(
                    severity="high",
                    title="Обнаружен mixed content",
                    description=(
                        f"На HTTPS-странице найдено {link_stats['mixed_content_count']} "
                        "HTTP-ресурсов или ссылок."
                    ),
                    recommendation="Перевести все внутренние ресурсы и ссылки на HTTPS."
                )
            )

        iframe_count = len(soup.find_all("iframe"))
        forms_count = len(soup.find_all("form"))
        missing_form_labels = self._count_inputs_missing_labels(soup)
        metrics.append(("technical_iframe_count", float(iframe_count), None))
        metrics.append(("forms_count", float(forms_count), None))
        metrics.append(("missing_form_labels_count", float(missing_form_labels), None))

        if iframe_count > 0:
            issues.append(
                TechnicalIssueData(
                    severity="low",
                    title="На странице используются iframe",
                    description=f"Найдено iframe: {iframe_count}.",
                    recommendation="Проверить необходимость iframe и их влияние на производительность, безопасность и индексацию."
                )
            )

        if missing_form_labels > 0:
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="Не все поля форм имеют явные label",
                    description=(
                        f"Найдено {missing_form_labels} полей формы без связанного label "
                        "или очевидного aria-label/aria-labelledby."
                    ),
                    recommendation="Добавить label или ARIA-атрибуты для всех пользовательских полей форм."
                )
            )

        canonical_url = self._extract_canonical_url(soup, base_url)
        has_canonical = bool(canonical_url)
        canonical_http_mismatch = bool(
            canonical_url
            and is_https
            and urlparse(canonical_url).scheme.lower() == "http"
        )
        metrics.append(("technical_has_canonical", 1.0 if has_canonical else 0.0, None))
        metrics.append(("canonical_http_mismatch", 1.0 if canonical_http_mismatch else 0.0, None))
        if canonical_http_mismatch:
            issues.append(
                TechnicalIssueData(
                    severity="medium",
                    title="Canonical указывает на HTTP-версию",
                    description=f"Canonical URL ведет на небезопасный адрес: {canonical_url}.",
                    recommendation="Обновить canonical на HTTPS-версию страницы."
                )
            )

        canonical_host_mismatch = self._canonical_host_mismatch(canonical_url, final_hostname)
        metrics.append(("canonical_host_mismatch", 1.0 if canonical_host_mismatch else 0.0, None))
        if canonical_host_mismatch:
            issues.append(
                TechnicalIssueData(
                    severity="low",
                    title="Canonical указывает на другой хост",
                    description=f"Canonical URL использует другой домен или поддомен: {canonical_url}.",
                    recommendation="Проверить, что canonical ссылается на целевую каноническую версию страницы."
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

    def _check_links(self, html: str, base_url: str) -> dict[str, int]:
        soup = BeautifulSoup(html, "html.parser")
        parsed_base = urlparse(base_url)
        base_hostname = parsed_base.hostname or ""
        internal_hrefs: list[str] = []
        external_hrefs: list[str] = []
        mailto_count = 0
        tel_count = 0
        mixed_content_count = 0

        for a_tag in soup.find_all("a", href=True):
            href = (a_tag.get("href") or "").strip()
            if not href:
                continue
            if href.startswith("#"):
                continue
            lower_href = href.lower()
            if lower_href.startswith("mailto:"):
                mailto_count += 1
                continue
            if lower_href.startswith("tel:"):
                tel_count += 1
                continue
            if lower_href.startswith("javascript:"):
                continue
            absolute_href = urljoin(base_url, href)
            parsed_href = urlparse(absolute_href)
            if (
                parsed_base.scheme.lower() == "https"
                and parsed_href.scheme.lower() == "http"
                and parsed_href.netloc
            ):
                mixed_content_count += 1
            if self._is_internal_url(absolute_href, base_hostname):
                internal_hrefs.append(absolute_href)
            else:
                external_hrefs.append(absolute_href)

        for tag_name, attr_name in (("img", "src"), ("script", "src"), ("iframe", "src")):
            for tag in soup.find_all(tag_name):
                resource_url = (tag.get(attr_name) or "").strip()
                if not resource_url:
                    continue
                absolute_url = urljoin(base_url, resource_url)
                parsed_resource = urlparse(absolute_url)
                if (
                    parsed_base.scheme.lower() == "https"
                    and parsed_resource.scheme.lower() == "http"
                    and parsed_resource.netloc
                ):
                    mixed_content_count += 1

        unique_internal = list(dict.fromkeys(internal_hrefs))
        unique_external = list(dict.fromkeys(external_hrefs))

        broken_internal = self._count_broken_links(unique_internal, limit=20)
        broken_external = self._count_broken_links(unique_external, limit=10)

        return {
            "links_count": len(unique_internal) + len(unique_external),
            "broken_links_count": broken_internal + broken_external,
            "internal_links_count": len(unique_internal),
            "external_links_count": len(unique_external),
            "broken_internal_links_count": broken_internal,
            "broken_external_links_count": broken_external,
            "mailto_links_count": mailto_count,
            "tel_links_count": tel_count,
            "mixed_content_count": mixed_content_count,
        }

    def _count_broken_links(self, links: list[str], limit: int) -> int:
        broken_links = 0
        for link in links[:limit]:
            if not self._is_link_ok(link):
                broken_links += 1
        return broken_links

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

    @staticmethod
    def _has_viewport_meta(soup: BeautifulSoup) -> bool:
        return soup.find("meta", attrs={"name": lambda value: value and value.lower() == "viewport"}) is not None

    @staticmethod
    def _has_compression_header(headers: dict[str, str]) -> bool:
        content_encoding = headers.get("content-encoding", "").lower()
        transfer_encoding = headers.get("transfer-encoding", "").lower()
        return any(
            encoding in content_encoding or encoding in transfer_encoding
            for encoding in ("gzip", "br", "deflate")
        )

    @staticmethod
    def _is_html_cacheable(cache_control: str) -> bool:
        lower_cache_control = cache_control.lower()
        if not lower_cache_control:
            return False
        blocking_directives = ("no-store", "private")
        return not any(directive in lower_cache_control for directive in blocking_directives)

    @staticmethod
    def _robots_directives_block_indexing(value: str) -> bool:
        lower_value = value.lower()
        return any(directive in lower_value for directive in ("noindex", "none"))

    def _check_www_consistency(self, final_url: str) -> bool:
        parsed = urlparse(final_url)
        hostname = parsed.hostname or ""
        if not hostname or hostname.count(".") < 1:
            return True

        if hostname.startswith("www."):
            alternate_host = hostname[4:]
        else:
            alternate_host = f"www.{hostname}"

        alternate_url = parsed._replace(netloc=alternate_host).geturl()
        try:
            with httpx.Client(
                timeout=min(self.timeout, 5.0),
                follow_redirects=True,
                headers={"User-Agent": "SiteAuditBot/1.0"},
            ) as client:
                response = client.head(alternate_url)
                if response.status_code == 405 or response.status_code >= 400:
                    response = client.get(alternate_url)
                if response.status_code >= 400:
                    return True
                return self._normalize_url(str(response.url)) == self._normalize_url(final_url)
        except httpx.RequestError:
            return True

    @staticmethod
    def _is_internal_url(url: str, base_hostname: str) -> bool:
        hostname = urlparse(url).hostname or ""
        return hostname == base_hostname

    @staticmethod
    def _extract_canonical_url(soup: BeautifulSoup, base_url: str) -> str | None:
        canonical_tag = soup.find("link", attrs={"rel": lambda value: value and "canonical" in value})
        href = canonical_tag.get("href") if canonical_tag else None
        if not href:
            return None
        return urljoin(base_url, href.strip())

    @staticmethod
    def _canonical_host_mismatch(canonical_url: str | None, final_hostname: str) -> bool:
        if not canonical_url or not final_hostname:
            return False
        canonical_hostname = urlparse(canonical_url).hostname or ""
        return canonical_hostname != final_hostname

    @staticmethod
    def _count_inputs_missing_labels(soup: BeautifulSoup) -> int:
        missing_labels = 0
        label_for_ids = {
            (label.get("for") or "").strip()
            for label in soup.find_all("label")
            if (label.get("for") or "").strip()
        }

        for form in soup.find_all("form"):
            for field in form.find_all(["input", "select", "textarea"]):
                if field.name == "input" and (field.get("type") or "").lower() in {
                    "hidden",
                    "submit",
                    "button",
                    "reset",
                    "image",
                }:
                    continue
                if field.get("aria-label") or field.get("aria-labelledby"):
                    continue
                field_id = (field.get("id") or "").strip()
                if field_id and field_id in label_for_ids:
                    continue
                if field.find_parent("label") is not None:
                    continue
                if field.get("title") or field.get("placeholder"):
                    continue
                missing_labels += 1

        return missing_labels

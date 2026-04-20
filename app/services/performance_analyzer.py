from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup


@dataclass
class PerformanceIssueData:
    severity: str
    title: str
    description: str
    recommendation: str


@dataclass
class PerformanceAnalysisResult:
    metrics: list[tuple[str, float, str | None]]
    issues: list[PerformanceIssueData]


class PerformanceAnalyzer:
    def analyze(self, html: str, response_time_ms: float) -> PerformanceAnalysisResult:
        soup = BeautifulSoup(html, "html.parser")

        issues: list[PerformanceIssueData] = []
        metrics: list[tuple[str, float, str | None]] = []

        html_size_bytes = len(html.encode("utf-8"))
        dom_nodes_count = len(soup.find_all())

        scripts = soup.find_all("script")
        external_scripts = [script for script in scripts if self._has_non_empty_attr(script, "src")]
        inline_scripts = [script for script in scripts if not self._has_non_empty_attr(script, "src")]
        async_scripts_count = sum(1 for script in external_scripts if script.has_attr("async"))
        defer_scripts_count = sum(1 for script in external_scripts if script.has_attr("defer"))
        render_blocking_scripts_count = sum(
            1 for script in external_scripts if self._is_render_blocking_script(script)
        )
        third_party_scripts_count = sum(
            1 for script in external_scripts if self._is_third_party_script(script.get("src", ""))
        )
        inline_script_bytes = sum(len(script.get_text().encode("utf-8")) for script in inline_scripts)

        stylesheet_links = [
            link for link in soup.find_all("link") if self._has_rel(link, "stylesheet")
        ]
        stylesheets_count = len(stylesheet_links)
        style_blocks = soup.find_all("style")
        inline_style_blocks_count = len(style_blocks)
        inline_style_bytes = sum(len(style.get_text().encode("utf-8")) for style in style_blocks)

        preload_links = [link for link in soup.find_all("link") if self._has_rel(link, "preload")]
        preconnect_links = [link for link in soup.find_all("link") if self._has_rel(link, "preconnect")]
        dns_prefetch_links = [
            link for link in soup.find_all("link") if self._has_rel(link, "dns-prefetch")
        ]
        prefetch_links = [link for link in soup.find_all("link") if self._has_rel(link, "prefetch")]
        modulepreload_links = [
            link for link in soup.find_all("link") if self._has_rel(link, "modulepreload")
        ]
        font_preload_count = sum(
            1
            for link in preload_links
            if (link.get("as") or "").strip().lower() == "font"
        )

        images = soup.find_all("img")
        images_count = len(images)
        lazy_images_count = sum(1 for img in images if self._is_lazy_image(img))
        srcset_images_count = sum(1 for img in images if self._has_non_empty_attr(img, "srcset"))
        images_with_dimensions_count = sum(1 for img in images if self._has_dimensions(img))
        lazy_images_ratio = self._ratio(lazy_images_count, images_count)
        srcset_usage_ratio = self._ratio(srcset_images_count, images_count)
        image_dimension_completeness_ratio = self._ratio(images_with_dimensions_count, images_count)

        iframe_count = len(soup.find_all("iframe"))

        overall_request_proxy_count = self._estimate_request_proxy_count(soup)

        metrics.append(("page_response_time", response_time_ms, "ms"))
        metrics.append(("page_size_bytes", float(html_size_bytes), "bytes"))
        metrics.append(("dom_nodes_count", float(dom_nodes_count), None))
        metrics.append(("scripts_count", float(len(scripts)), None))
        metrics.append(("external_scripts_count", float(len(external_scripts)), None))
        metrics.append(("inline_scripts_count", float(len(inline_scripts)), None))
        metrics.append(("inline_script_bytes", float(inline_script_bytes), "bytes"))
        metrics.append(("async_scripts_count", float(async_scripts_count), None))
        metrics.append(("defer_scripts_count", float(defer_scripts_count), None))
        metrics.append(("render_blocking_scripts_count", float(render_blocking_scripts_count), None))
        metrics.append(("third_party_scripts_count", float(third_party_scripts_count), None))
        metrics.append(("stylesheets_count", float(stylesheets_count), None))
        metrics.append(("inline_style_blocks_count", float(inline_style_blocks_count), None))
        metrics.append(("inline_style_bytes", float(inline_style_bytes), "bytes"))
        metrics.append(("preload_links_count", float(len(preload_links)), None))
        metrics.append(("preconnect_links_count", float(len(preconnect_links)), None))
        metrics.append(("dns_prefetch_links_count", float(len(dns_prefetch_links)), None))
        metrics.append(("prefetch_links_count", float(len(prefetch_links)), None))
        metrics.append(("modulepreload_links_count", float(len(modulepreload_links)), None))
        metrics.append(("resource_hints_count", float(self._count_resource_hints(soup)), None))
        metrics.append(("font_preload_count", float(font_preload_count), None))
        metrics.append(("page_images_count", float(images_count), None))
        metrics.append(("lazy_images_count", float(lazy_images_count), None))
        metrics.append(("lazy_images_ratio", lazy_images_ratio, "%"))
        metrics.append(("srcset_images_count", float(srcset_images_count), None))
        metrics.append(("srcset_usage_ratio", srcset_usage_ratio, "%"))
        metrics.append(("images_with_dimensions_count", float(images_with_dimensions_count), None))
        metrics.append(
            ("image_dimension_completeness_ratio", image_dimension_completeness_ratio, "%")
        )
        metrics.append(("performance_iframe_count", float(iframe_count), None))
        metrics.append(("overall_request_proxy_count", float(overall_request_proxy_count), None))

        if response_time_ms > 3000:
            issues.append(
                PerformanceIssueData(
                    severity="high",
                    title="Очень медленный ответ страницы",
                    description=f"Время ответа страницы составляет {response_time_ms} мс.",
                    recommendation="Оптимизировать серверную обработку, кэширование и сетевую доставку контента."
                )
            )
        elif response_time_ms > 1500:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Замедленный ответ страницы",
                    description=f"Время ответа страницы составляет {response_time_ms} мс.",
                    recommendation="Сократить время ответа сервера и оптимизировать загрузку страницы."
                )
            )

        if html_size_bytes > 500_000:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Большой размер HTML",
                    description=f"Размер HTML-документа составляет {html_size_bytes} байт.",
                    recommendation="Сократить объем HTML, удалить лишнюю разметку и минимизировать шаблоны."
                )
            )
        elif html_size_bytes > 200_000:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="HTML больше рекомендуемого",
                    description=f"Размер HTML-документа составляет {html_size_bytes} байт.",
                    recommendation="Проверить возможность уменьшения размера HTML-документа."
                )
            )

        if dom_nodes_count > 3000:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Очень большой DOM",
                    description=f"На странице найдено {dom_nodes_count} HTML-узлов.",
                    recommendation="Сократить глубину и объем DOM, убрать лишние контейнеры и повторяющиеся блоки."
                )
            )
        elif dom_nodes_count > 1500:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Увеличенный размер DOM",
                    description=f"На странице найдено {dom_nodes_count} HTML-узлов.",
                    recommendation="Проверить, можно ли упростить структуру DOM."
                )
            )

        if len(scripts) > 20:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Слишком много скриптов",
                    description=f"На странице найдено {len(scripts)} тегов script.",
                    recommendation="Сократить количество скриптов, объединить или отложить их загрузку."
                )
            )
        elif len(scripts) > 10:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Повышенное количество скриптов",
                    description=f"На странице найдено {len(scripts)} тегов script.",
                    recommendation="Проверить необходимость всех подключенных скриптов."
                )
            )

        if inline_script_bytes > 50_000:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Большой объем inline JavaScript",
                    description=f"Встроенные скрипты занимают {inline_script_bytes} байт.",
                    recommendation="Вынести тяжелый inline JavaScript во внешние файлы или сократить его объем."
                )
            )
        elif inline_script_bytes > 15_000:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Заметный объем inline JavaScript",
                    description=f"Встроенные скрипты занимают {inline_script_bytes} байт.",
                    recommendation="Проверить, можно ли уменьшить объем встроенного JavaScript."
                )
            )

        if inline_style_bytes > 20_000:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Большой объем inline CSS",
                    description=f"Встроенные стили занимают {inline_style_bytes} байт.",
                    recommendation="Сократить объем inline CSS и по возможности вынести его в кешируемые стили."
                )
            )
        elif inline_style_bytes > 8_000:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Заметный объем inline CSS",
                    description=f"Встроенные стили занимают {inline_style_bytes} байт.",
                    recommendation="Проверить возможность уменьшения встроенных стилей."
                )
            )

        if render_blocking_scripts_count >= 3:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Обнаружены блокирующие рендеринг скрипты",
                    description=(
                        f"Найдено {render_blocking_scripts_count} внешних script без async/defer "
                        "в потенциально критичной части документа."
                    ),
                    recommendation="Для некритичных скриптов использовать async/defer или переносить их ниже по документу."
                )
            )
        elif render_blocking_scripts_count > 0:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Есть потенциально блокирующие скрипты",
                    description=(
                        f"Найдено {render_blocking_scripts_count} внешних script без async/defer."
                    ),
                    recommendation="Проверить, можно ли сделать загрузку этих скриптов неблокирующей."
                )
            )

        if third_party_scripts_count >= 5:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Много сторонних скриптов",
                    description=(
                        f"Найдено {third_party_scripts_count} внешних script с признаками сторонних сервисов."
                    ),
                    recommendation="Проверить необходимость сторонних интеграций и отложить загрузку необязательных скриптов."
                )
            )
        elif third_party_scripts_count >= 2:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Есть сторонние скрипты",
                    description=(
                        f"Найдено {third_party_scripts_count} внешних script с признаками сторонних сервисов."
                    ),
                    recommendation="Оценить влияние сторонних скриптов на загрузку и стабильность страницы."
                )
            )

        if images_count > 30:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Слишком много изображений на странице",
                    description=f"На странице найдено {images_count} изображений.",
                    recommendation="Оптимизировать изображения, использовать lazy loading и уменьшить их количество."
                )
            )
        elif images_count > 15:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Большое количество изображений",
                    description=f"На странице найдено {images_count} изображений.",
                    recommendation="Проверить оптимизацию и необходимость всех изображений."
                )
            )

        if images_count >= 6 and lazy_images_ratio < 40.0:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Недостаточно lazy loading для изображений",
                    description=(
                        f"Только {lazy_images_count} из {images_count} изображений используют lazy loading."
                    ),
                    recommendation="Добавить loading='lazy' для некритичных изображений вне первого экрана."
                )
            )
        elif images_count >= 3 and lazy_images_ratio < 70.0:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Часть изображений загружается без lazy loading",
                    description=(
                        f"Только {lazy_images_count} из {images_count} изображений используют lazy loading."
                    ),
                    recommendation="Проверить, какие изображения можно загружать лениво."
                )
            )

        if images_count >= 6 and srcset_usage_ratio < 30.0:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Низкое использование адаптивных изображений",
                    description=(
                        f"Только {srcset_images_count} из {images_count} изображений используют srcset."
                    ),
                    recommendation="Для крупных и контентных изображений рассмотреть использование srcset и sizes."
                )
            )

        if images_count >= 4 and image_dimension_completeness_ratio < 50.0:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="У изображений часто не заданы размеры",
                    description=(
                        f"Только у {images_with_dimensions_count} из {images_count} изображений указаны width и height."
                    ),
                    recommendation="Явно указывать размеры изображений, чтобы снизить риск сдвигов макета."
                )
            )
        elif images_count > 0 and image_dimension_completeness_ratio < 80.0:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Не у всех изображений заданы размеры",
                    description=(
                        f"Только у {images_with_dimensions_count} из {images_count} изображений указаны width и height."
                    ),
                    recommendation="Проверить изображения без width и height и добавить размеры там, где это возможно."
                )
            )

        if stylesheets_count >= 8 and len(preload_links) == 0:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Нет preload для критичных ресурсов",
                    description=(
                        f"На странице найдено {stylesheets_count} таблиц стилей, но не найдено ни одного preload."
                    ),
                    recommendation="Проверить, есть ли смысл добавить preload для критичных шрифтов, стилей или hero-ресурсов."
                )
            )

        if third_party_scripts_count > 0 and len(preconnect_links) == 0 and len(dns_prefetch_links) == 0:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Нет resource hints для внешних источников",
                    description=(
                        "Обнаружены сторонние скрипты, но не найдено preconnect или dns-prefetch подсказок."
                    ),
                    recommendation="Для действительно важных внешних доменов рассмотреть preconnect или dns-prefetch."
                )
            )

        if iframe_count >= 3:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Несколько iframe на странице",
                    description=f"На странице найдено {iframe_count} iframe.",
                    recommendation="Проверить необходимость всех iframe и влияние встраиваемых сервисов на производительность."
                )
            )

        return PerformanceAnalysisResult(metrics=metrics, issues=issues)

    @staticmethod
    def _count_resource_hints(soup: BeautifulSoup) -> int:
        hints = {"preload", "preconnect", "dns-prefetch", "prefetch", "modulepreload"}
        count = 0
        for link in soup.find_all("link"):
            rel_values = PerformanceAnalyzer._get_rel_values(link)
            if any(rel_value in hints for rel_value in rel_values):
                count += 1
        return count

    @staticmethod
    def _estimate_request_proxy_count(soup: BeautifulSoup) -> int:
        count = 0
        count += sum(1 for script in soup.find_all("script") if PerformanceAnalyzer._has_non_empty_attr(script, "src"))
        count += sum(1 for link in soup.find_all("link") if PerformanceAnalyzer._has_non_empty_attr(link, "href"))
        count += sum(1 for img in soup.find_all("img") if PerformanceAnalyzer._has_non_empty_attr(img, "src"))
        count += sum(1 for source in soup.find_all("source") if PerformanceAnalyzer._has_source_candidate(source))
        count += sum(1 for iframe in soup.find_all("iframe") if PerformanceAnalyzer._has_non_empty_attr(iframe, "src"))
        count += sum(1 for audio in soup.find_all("audio") if PerformanceAnalyzer._has_non_empty_attr(audio, "src"))
        count += sum(1 for video in soup.find_all("video") if PerformanceAnalyzer._has_non_empty_attr(video, "src"))
        count += sum(1 for video in soup.find_all("video") if PerformanceAnalyzer._has_non_empty_attr(video, "poster"))
        count += sum(1 for embed in soup.find_all("embed") if PerformanceAnalyzer._has_non_empty_attr(embed, "src"))
        count += sum(1 for obj in soup.find_all("object") if PerformanceAnalyzer._has_non_empty_attr(obj, "data"))
        return count

    @staticmethod
    def _get_rel_values(tag) -> list[str]:
        rel_attr = tag.get("rel")
        if rel_attr is None:
            return []
        if isinstance(rel_attr, str):
            values = rel_attr.split()
        else:
            values = list(rel_attr)
        return [value.strip().lower() for value in values if value and value.strip()]

    @staticmethod
    def _has_rel(tag, rel_name: str) -> bool:
        return rel_name.lower() in PerformanceAnalyzer._get_rel_values(tag)

    @staticmethod
    def _has_non_empty_attr(tag, attr_name: str) -> bool:
        value = tag.get(attr_name)
        return isinstance(value, str) and bool(value.strip())

    @staticmethod
    def _has_dimensions(img_tag) -> bool:
        width = img_tag.get("width")
        height = img_tag.get("height")
        return isinstance(width, str) and bool(width.strip()) and isinstance(height, str) and bool(height.strip())

    @staticmethod
    def _is_lazy_image(img_tag) -> bool:
        loading = (img_tag.get("loading") or "").strip().lower()
        if loading == "lazy":
            return True

        data_src = (img_tag.get("data-src") or "").strip()
        data_srcset = (img_tag.get("data-srcset") or "").strip()
        return bool(data_src or data_srcset)

    @staticmethod
    def _is_render_blocking_script(script_tag) -> bool:
        src = (script_tag.get("src") or "").strip()
        script_type = (script_tag.get("type") or "").strip().lower()
        if not src:
            return False
        if script_tag.has_attr("async") or script_tag.has_attr("defer"):
            return False
        if script_type == "module":
            return False

        parent = script_tag.parent
        while parent is not None:
            if getattr(parent, "name", None) == "head":
                return True
            parent = parent.parent

        return False

    @staticmethod
    def _is_third_party_script(src: str) -> bool:
        normalized_src = src.strip().lower()
        if not normalized_src:
            return False
        if normalized_src.startswith("//"):
            return True
        if normalized_src.startswith("http://") or normalized_src.startswith("https://"):
            hostname = urlparse(normalized_src).hostname or ""
            if hostname and hostname not in {"localhost", "127.0.0.1"}:
                return True

        third_party_markers = (
            "googletagmanager",
            "google-analytics",
            "doubleclick",
            "facebook",
            "connect.facebook.net",
            "yandex",
            "metrika",
            "vk.com",
            "mc.yandex",
            "cdn.jsdelivr.net",
            "unpkg.com",
            "cloudflare",
            "hotjar",
            "intercom",
            "tawk.to",
            "segment",
            "amplitude",
            "mixpanel",
        )
        return any(marker in normalized_src for marker in third_party_markers)

    @staticmethod
    def _has_source_candidate(tag) -> bool:
        return PerformanceAnalyzer._has_non_empty_attr(tag, "src") or PerformanceAnalyzer._has_non_empty_attr(
            tag, "srcset"
        )

    @staticmethod
    def _ratio(part: int, total: int) -> float:
        if total == 0:
            return 0.0
        return round((part / total) * 100, 2)

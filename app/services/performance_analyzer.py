from dataclasses import dataclass

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
        scripts_count = len(soup.find_all("script"))
        stylesheets_count = len(soup.find_all("link", rel="stylesheet"))
        images_count = len(soup.find_all("img"))

        metrics.append(("page_response_time", response_time_ms, "ms"))
        metrics.append(("page_size_bytes", float(html_size_bytes), "bytes"))
        metrics.append(("scripts_count", float(scripts_count), None))
        metrics.append(("stylesheets_count", float(stylesheets_count), None))
        metrics.append(("page_images_count", float(images_count), None))

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

        if scripts_count > 20:
            issues.append(
                PerformanceIssueData(
                    severity="medium",
                    title="Слишком много скриптов",
                    description=f"На странице найдено {scripts_count} тегов script.",
                    recommendation="Сократить количество скриптов, объединить или отложить их загрузку."
                )
            )
        elif scripts_count > 10:
            issues.append(
                PerformanceIssueData(
                    severity="low",
                    title="Повышенное количество скриптов",
                    description=f"На странице найдено {scripts_count} тегов script.",
                    recommendation="Проверить необходимость всех подключенных скриптов."
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

        return PerformanceAnalysisResult(metrics=metrics, issues=issues)
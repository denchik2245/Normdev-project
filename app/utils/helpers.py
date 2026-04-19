from datetime import datetime


def get_metric_display_name(metric_name: str) -> str:
    metric_names = {
        "status_code": "HTTP-статус страницы",
        "response_time": "Время ответа страницы",
        "html_size": "Размер HTML",
        "title_length": "Длина title",
        "meta_description_length": "Длина meta description",
        "h1_count": "Количество H1",
        "has_canonical": "Наличие canonical",
        "has_robots_meta": "Наличие meta robots",
        "images_count": "Количество изображений",
        "images_without_alt": "Изображения без alt",
        "uses_https": "Использование HTTPS",
        "has_redirect": "Наличие редиректа",
        "main_status_code": "Основной HTTP-статус",
        "robots_txt_available": "Доступность robots.txt",
        "sitemap_xml_available": "Доступность sitemap.xml",
        "links_count": "Количество ссылок",
        "broken_links_count": "Количество битых ссылок",
        "has_server_header": "Наличие server header",
        "page_response_time": "Время ответа (performance)",
        "page_size_bytes": "Размер страницы",
        "scripts_count": "Количество скриптов",
        "stylesheets_count": "Количество CSS-файлов",
        "page_images_count": "Количество изображений на странице",
    }

    return metric_names.get(metric_name, metric_name)


def format_metric_value(metric_name: str, metric_value: float, unit: str | None) -> str:
    boolean_metrics = {
        "has_canonical",
        "has_robots_meta",
        "uses_https",
        "has_redirect",
        "robots_txt_available",
        "sitemap_xml_available",
        "has_server_header",
    }

    if metric_name in boolean_metrics:
        return "Да" if metric_value == 1 else "Нет"

    if unit == "ms":
        return f"{metric_value:.2f}"
    if unit == "bytes":
        return f"{int(metric_value)}"
    if unit == "chars":
        return f"{int(metric_value)}"

    if metric_value.is_integer():
        return str(int(metric_value))

    return f"{metric_value:.2f}"


def get_score_label(score: float | None) -> str:
    if score is None:
        return "Нет оценки"
    if score >= 90:
        return "Отлично"
    if score >= 75:
        return "Хорошо"
    if score >= 50:
        return "Удовлетворительно"
    return "Плохо"


def get_score_class(score: float | None) -> str:
    if score is None:
        return "score-none"
    if score >= 90:
        return "score-excellent"
    if score >= 75:
        return "score-good"
    if score >= 50:
        return "score-warning"
    return "score-bad"


def get_status_label(status: str) -> str:
    labels = {
        "completed": "Завершен",
        "failed": "Ошибка",
        "running": "Выполняется",
        "pending": "Ожидает",
    }
    return labels.get(status, status)


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d.%m.%Y %H:%M")
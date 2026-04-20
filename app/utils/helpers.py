from datetime import datetime


SEO_METRIC_NAMES = {
    "title_length",
    "meta_description_length",
    "h1_count",
    "h2_count",
    "h3_count",
    "heading_level_skips",
    "has_canonical",
    "seo_has_canonical",
    "canonical_is_absolute",
    "has_robots_meta",
    "has_meta_keywords",
    "has_lang",
    "has_favicon",
    "open_graph_basic_count",
    "has_open_graph_basics",
    "structured_data_count",
    "has_structured_data",
    "seo_internal_links_count",
    "seo_external_links_count",
    "empty_anchors_count",
    "duplicate_anchors_count",
    "images_count",
    "images_without_alt",
    "images_lazy_loaded",
    "images_lazy_loaded_ratio",
    "text_length",
    "text_to_html_ratio",
}

TECHNICAL_METRIC_NAMES = {
    "status_code",
    "response_time",
    "html_size",
    "uses_https",
    "has_redirect",
    "main_status_code",
    "has_html_content_type",
    "has_charset_in_content_type",
    "has_viewport_meta",
    "has_compression",
    "has_cache_control",
    "html_cacheable",
    "has_hsts",
    "has_x_content_type_options",
    "has_x_frame_options",
    "has_content_security_policy",
    "has_referrer_policy",
    "has_permissions_policy",
    "has_x_robots_tag",
    "x_robots_tag_blocks_indexing",
    "www_host_consistent",
    "robots_txt_available",
    "sitemap_xml_available",
    "links_count",
    "broken_links_count",
    "technical_internal_links_count",
    "technical_external_links_count",
    "broken_internal_links_count",
    "broken_external_links_count",
    "mailto_links_count",
    "tel_links_count",
    "mixed_content_count",
    "technical_iframe_count",
    "forms_count",
    "missing_form_labels_count",
    "technical_has_canonical",
    "canonical_http_mismatch",
    "canonical_host_mismatch",
    "has_server_header",
}

PERFORMANCE_METRIC_NAMES = {
    "page_response_time",
    "page_size_bytes",
    "dom_nodes_count",
    "scripts_count",
    "external_scripts_count",
    "inline_scripts_count",
    "inline_script_bytes",
    "async_scripts_count",
    "defer_scripts_count",
    "render_blocking_scripts_count",
    "third_party_scripts_count",
    "stylesheets_count",
    "inline_style_blocks_count",
    "inline_style_bytes",
    "preload_links_count",
    "preconnect_links_count",
    "dns_prefetch_links_count",
    "prefetch_links_count",
    "modulepreload_links_count",
    "resource_hints_count",
    "font_preload_count",
    "page_images_count",
    "lazy_images_count",
    "lazy_images_ratio",
    "srcset_images_count",
    "srcset_usage_ratio",
    "images_with_dimensions_count",
    "image_dimension_completeness_ratio",
    "performance_iframe_count",
    "overall_request_proxy_count",
}


def get_metric_category(metric_name: str) -> str:
    if metric_name in SEO_METRIC_NAMES:
        return "seo"
    if metric_name in TECHNICAL_METRIC_NAMES:
        return "technical"
    if metric_name in PERFORMANCE_METRIC_NAMES:
        return "performance"
    return "other"


def get_category_label(category: str) -> str:
    labels = {
        "seo": "SEO",
        "technical": "Технические",
        "performance": "Производительность",
        "other": "Прочее",
    }
    return labels.get(category, category)


def group_metrics_by_category(metrics) -> dict[str, list]:
    grouped = {
        "seo": [],
        "technical": [],
        "performance": [],
        "other": [],
    }

    for metric in metrics:
        grouped[get_metric_category(metric.metric_name)].append(metric)

    return grouped


def calculate_category_score(issues) -> float:
    score = 100.0

    for issue in issues:
        if issue.severity == "high":
            score -= 10
        elif issue.severity == "medium":
            score -= 5
        elif issue.severity == "low":
            score -= 2

    if score < 0:
        score = 0.0

    return round(score, 2)


def get_metric_severity(metric_name: str, metric_value: float) -> str:
    if metric_name in {
        "seo_has_canonical",
        "canonical_is_absolute",
        "has_robots_meta",
        "has_lang",
        "has_favicon",
        "has_open_graph_basics",
        "has_structured_data",
        "uses_https",
        "has_html_content_type",
        "has_charset_in_content_type",
        "has_viewport_meta",
        "has_compression",
        "has_cache_control",
        "html_cacheable",
        "has_hsts",
        "has_x_content_type_options",
        "has_x_frame_options",
        "has_content_security_policy",
        "has_referrer_policy",
        "has_permissions_policy",
        "www_host_consistent",
        "robots_txt_available",
        "sitemap_xml_available",
        "technical_has_canonical",
    }:
        return "" if metric_value == 1 else "high"

    if metric_name in {
        "x_robots_tag_blocks_indexing",
        "canonical_http_mismatch",
        "canonical_host_mismatch",
    }:
        return "" if metric_value == 0 else "high"

    if metric_name == "title_length":
        if metric_value == 0:
            return "high"
        if metric_value < 30:
            return "medium"
        if metric_value > 60:
            return "low"
        return ""

    if metric_name == "meta_description_length":
        if metric_value == 0:
            return "high"
        if metric_value < 120:
            return "medium"
        if metric_value > 160:
            return "low"
        return ""

    if metric_name == "h1_count":
        if metric_value == 0:
            return "high"
        if metric_value > 1:
            return "medium"
        return ""

    if metric_name in {"h2_count", "h3_count"}:
        return "" if metric_value > 0 else "low"

    if metric_name in {
        "heading_level_skips",
        "empty_anchors_count",
        "duplicate_anchors_count",
        "broken_links_count",
        "broken_internal_links_count",
        "broken_external_links_count",
        "missing_form_labels_count",
        "mixed_content_count",
        "render_blocking_scripts_count",
    }:
        if metric_value == 0:
            return ""
        if metric_value >= 3:
            return "high"
        return "medium"

    if metric_name in {
        "images_without_alt",
        "forms_count",
        "technical_iframe_count",
        "performance_iframe_count",
        "third_party_scripts_count",
    }:
        if metric_value == 0:
            return ""
        if metric_value >= 3:
            return "medium"
        return "low"

    if metric_name in {"text_length"}:
        if metric_value < 300:
            return "medium"
        if metric_value < 600:
            return "low"
        return ""

    if metric_name in {"text_to_html_ratio"}:
        if metric_value < 10:
            return "low"
        return ""

    if metric_name in {"images_lazy_loaded_ratio", "lazy_images_ratio"}:
        if metric_value < 40:
            return "high"
        if metric_value < 70:
            return "medium"
        return ""

    if metric_name in {"srcset_usage_ratio"}:
        if metric_value < 30:
            return "low"
        return ""

    if metric_name in {"image_dimension_completeness_ratio"}:
        if metric_value < 50:
            return "medium"
        if metric_value < 80:
            return "low"
        return ""

    if metric_name in {"response_time", "page_response_time"}:
        if metric_value > 3000:
            return "high"
        if metric_value > 1500:
            return "medium"
        return ""

    if metric_name in {"html_size", "page_size_bytes", "inline_script_bytes"}:
        if metric_value > 500_000:
            return "medium"
        if metric_value > 200_000:
            return "low"
        return ""

    if metric_name == "inline_style_bytes":
        if metric_value > 20_000:
            return "medium"
        if metric_value > 8_000:
            return "low"
        return ""

    if metric_name == "dom_nodes_count":
        if metric_value > 3000:
            return "medium"
        if metric_value > 1500:
            return "low"
        return ""

    if metric_name in {"scripts_count"}:
        if metric_value > 20:
            return "medium"
        if metric_value > 10:
            return "low"
        return ""

    if metric_name in {"images_count", "page_images_count"}:
        if metric_value > 30:
            return "medium"
        if metric_value > 15:
            return "low"
        return ""

    if metric_name in {"main_status_code", "status_code"}:
        if metric_value >= 500:
            return "high"
        if metric_value >= 400:
            return "high"
        if metric_value >= 300:
            return "medium"
        return ""

    return ""


def count_problematic_metrics(metrics) -> int:
    return sum(
        1
        for metric in metrics
        if get_metric_severity(metric.metric_name, metric.metric_value)
    )


def get_metric_catalog() -> dict[str, dict[str, object]]:
    return {
        "seo": {
            "title": "SEO",
            "description": "Проверки структуры страницы, индексации и базовой поисковой оптимизации.",
            "metrics": [
                "Длина title",
                "Длина meta description",
                "Количество H1, H2, H3",
                "Пропуски уровней заголовков",
                "Наличие canonical",
                "Наличие meta robots",
                "Наличие lang и favicon",
                "Open Graph и structured data",
                "Внутренние и внешние SEO-ссылки",
                "Пустые и дублирующиеся анкоры",
                "Изображения без alt",
                "Доля lazy loading у изображений",
                "Объем текста и соотношение текста к HTML",
            ],
        },
        "technical": {
            "title": "Технические",
            "description": "Проверки доступности, безопасности, заголовков ответа и технического здоровья сайта.",
            "metrics": [
                "HTTP-статусы и редиректы",
                "HTTPS и HSTS",
                "Content-Type и charset",
                "Meta viewport",
                "Compression и Cache-Control",
                "Security headers",
                "X-Robots-Tag",
                "www/non-www согласованность",
                "robots.txt и sitemap.xml",
                "Количество ссылок и битые ссылки",
                "Mixed content",
                "Формы и поля без label",
                "Технические проверки canonical",
            ],
        },
        "performance": {
            "title": "Производительность",
            "description": "Проверки веса страницы, DOM, скриптов, изображений и подсказок загрузки.",
            "metrics": [
                "Время ответа страницы",
                "Размер страницы и HTML",
                "Количество DOM-узлов",
                "Количество script и CSS",
                "Внешние и inline-скрипты",
                "Async и defer-скрипты",
                "Render-blocking scripts",
                "Third-party scripts",
                "Inline CSS и JS",
                "Preload, preconnect и resource hints",
                "Количество изображений",
                "Lazy loading и srcset",
                "Размеры изображений и iframe",
            ],
        },
    }


def get_metric_display_name(metric_name: str) -> str:
    metric_names = {
        "status_code": "HTTP-статус страницы",
        "response_time": "Время ответа страницы",
        "html_size": "Размер HTML",
        "title_length": "Длина title",
        "meta_description_length": "Длина meta description",
        "h1_count": "Количество H1",
        "h2_count": "Количество H2",
        "h3_count": "Количество H3",
        "heading_level_skips": "Пропуски уровней заголовков",
        "has_canonical": "Наличие canonical",
        "seo_has_canonical": "SEO: наличие canonical",
        "canonical_is_absolute": "Canonical является абсолютным URL",
        "has_robots_meta": "Наличие meta robots",
        "has_meta_keywords": "Наличие meta keywords",
        "has_lang": "Наличие атрибута lang",
        "has_favicon": "Наличие favicon",
        "open_graph_basic_count": "Количество базовых Open Graph тегов",
        "has_open_graph_basics": "Наличие базовых Open Graph тегов",
        "structured_data_count": "Количество структурированных данных",
        "has_structured_data": "Наличие структурированных данных",
        "seo_internal_links_count": "SEO: количество внутренних ссылок",
        "seo_external_links_count": "SEO: количество внешних ссылок",
        "empty_anchors_count": "Количество пустых ссылок",
        "duplicate_anchors_count": "Количество дублирующихся ссылок",
        "images_count": "Количество изображений",
        "images_without_alt": "Изображения без alt",
        "images_lazy_loaded": "Изображения с lazy loading",
        "images_lazy_loaded_ratio": "Доля изображений с lazy loading",
        "text_length": "Объем текстового контента",
        "text_to_html_ratio": "Соотношение текста к HTML",
        "uses_https": "Использование HTTPS",
        "has_redirect": "Наличие редиректа",
        "main_status_code": "Основной HTTP-статус",
        "has_html_content_type": "Корректный Content-Type HTML",
        "has_charset_in_content_type": "Наличие charset в Content-Type",
        "has_viewport_meta": "Наличие meta viewport",
        "has_compression": "Наличие HTTP-сжатия",
        "has_cache_control": "Наличие Cache-Control",
        "html_cacheable": "HTML допускает кеширование",
        "has_hsts": "Наличие HSTS",
        "has_x_content_type_options": "Наличие X-Content-Type-Options",
        "has_x_frame_options": "Наличие X-Frame-Options",
        "has_content_security_policy": "Наличие Content-Security-Policy",
        "has_referrer_policy": "Наличие Referrer-Policy",
        "has_permissions_policy": "Наличие Permissions-Policy",
        "has_x_robots_tag": "Наличие X-Robots-Tag",
        "x_robots_tag_blocks_indexing": "X-Robots-Tag блокирует индексацию",
        "www_host_consistent": "Согласованность www/non-www",
        "robots_txt_available": "Доступность robots.txt",
        "sitemap_xml_available": "Доступность sitemap.xml",
        "links_count": "Количество ссылок",
        "broken_links_count": "Количество битых ссылок",
        "technical_internal_links_count": "Технические: внутренние ссылки",
        "technical_external_links_count": "Технические: внешние ссылки",
        "broken_internal_links_count": "Битые внутренние ссылки",
        "broken_external_links_count": "Битые внешние ссылки",
        "mailto_links_count": "Количество mailto-ссылок",
        "tel_links_count": "Количество tel-ссылок",
        "mixed_content_count": "Количество mixed content ресурсов",
        "technical_iframe_count": "Технические: количество iframe",
        "forms_count": "Количество форм",
        "missing_form_labels_count": "Поля форм без label",
        "technical_has_canonical": "Технические: наличие canonical",
        "canonical_http_mismatch": "Canonical указывает на HTTP",
        "canonical_host_mismatch": "Canonical указывает на другой хост",
        "has_server_header": "Наличие server header",
        "page_response_time": "Время ответа (performance)",
        "page_size_bytes": "Размер страницы",
        "dom_nodes_count": "Количество DOM-узлов",
        "scripts_count": "Количество скриптов",
        "external_scripts_count": "Количество внешних скриптов",
        "inline_scripts_count": "Количество inline-скриптов",
        "inline_script_bytes": "Объем inline JavaScript",
        "async_scripts_count": "Количество async-скриптов",
        "defer_scripts_count": "Количество defer-скриптов",
        "render_blocking_scripts_count": "Потенциально блокирующие скрипты",
        "third_party_scripts_count": "Количество сторонних скриптов",
        "stylesheets_count": "Количество CSS-файлов",
        "inline_style_blocks_count": "Количество inline style-блоков",
        "inline_style_bytes": "Объем inline CSS",
        "preload_links_count": "Количество preload-подсказок",
        "preconnect_links_count": "Количество preconnect-подсказок",
        "dns_prefetch_links_count": "Количество dns-prefetch-подсказок",
        "prefetch_links_count": "Количество prefetch-подсказок",
        "modulepreload_links_count": "Количество modulepreload-подсказок",
        "resource_hints_count": "Общее количество resource hints",
        "font_preload_count": "Количество preload для шрифтов",
        "page_images_count": "Количество изображений на странице",
        "lazy_images_count": "Изображения с lazy loading",
        "lazy_images_ratio": "Доля изображений с lazy loading",
        "srcset_images_count": "Изображения с srcset",
        "srcset_usage_ratio": "Доля изображений с srcset",
        "images_with_dimensions_count": "Изображения с width и height",
        "image_dimension_completeness_ratio": "Доля изображений с размерами",
        "performance_iframe_count": "Performance: количество iframe",
        "overall_request_proxy_count": "Оценка числа загружаемых ресурсов",
    }

    return metric_names.get(metric_name, metric_name)


def format_metric_value(metric_name: str, metric_value: float, unit: str | None) -> str:
    boolean_metrics = {
        "has_canonical",
        "seo_has_canonical",
        "canonical_is_absolute",
        "has_robots_meta",
        "has_meta_keywords",
        "has_lang",
        "has_favicon",
        "has_open_graph_basics",
        "has_structured_data",
        "uses_https",
        "has_redirect",
        "has_html_content_type",
        "has_charset_in_content_type",
        "has_viewport_meta",
        "has_compression",
        "has_cache_control",
        "html_cacheable",
        "has_hsts",
        "has_x_content_type_options",
        "has_x_frame_options",
        "has_content_security_policy",
        "has_referrer_policy",
        "has_permissions_policy",
        "has_x_robots_tag",
        "x_robots_tag_blocks_indexing",
        "www_host_consistent",
        "robots_txt_available",
        "sitemap_xml_available",
        "technical_has_canonical",
        "canonical_http_mismatch",
        "canonical_host_mismatch",
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
    if unit in {"percent", "%"}:
        return f"{metric_value:.2f}"

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

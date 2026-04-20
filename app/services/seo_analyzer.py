import re
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup


@dataclass
class SEOIssueData:
    severity: str
    title: str
    description: str
    recommendation: str


@dataclass
class SEOAnalysisResult:
    metrics: list[tuple[str, float, str | None]]
    issues: list[SEOIssueData]


class SEOAnalyzer:
    @staticmethod
    def _get_meta_content(soup: BeautifulSoup, name: str) -> str:
        for meta_tag in soup.find_all("meta"):
            meta_name = (meta_tag.get("name") or "").strip().lower()
            if meta_name == name.lower():
                return (meta_tag.get("content") or "").strip()
        return ""

    @staticmethod
    def _get_property_content(soup: BeautifulSoup, prop: str) -> str:
        for meta_tag in soup.find_all("meta"):
            meta_property = (meta_tag.get("property") or "").strip().lower()
            if meta_property == prop.lower():
                return (meta_tag.get("content") or "").strip()
        return ""

    @staticmethod
    def _link_rel_contains(tag, rel_value: str) -> bool:
        if tag.name != "link":
            return False

        rel_attr = tag.get("rel") or []
        if isinstance(rel_attr, str):
            rel_values = [part.strip().lower() for part in rel_attr.split() if part.strip()]
        else:
            rel_values = [str(part).strip().lower() for part in rel_attr if str(part).strip()]

        return rel_value.lower() in rel_values

    @staticmethod
    def _is_internal_href(href: str) -> bool:
        parsed = urlparse(href)
        if not href or href.startswith("#"):
            return False
        if parsed.scheme in {"mailto", "tel", "javascript", "data"}:
            return False
        return not parsed.scheme and not parsed.netloc

    @staticmethod
    def _is_external_href(href: str) -> bool:
        parsed = urlparse(href)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @staticmethod
    def _extract_visible_text(soup: BeautifulSoup) -> str:
        excluded_parents = {
            "script",
            "style",
            "noscript",
            "template",
            "head",
            "title",
            "meta",
            "link",
        }
        parts: list[str] = []

        for string in soup.find_all(string=True):
            parent = getattr(string, "parent", None)
            if parent and parent.name in excluded_parents:
                continue

            text = re.sub(r"\s+", " ", str(string)).strip()
            if text:
                parts.append(text)

        return " ".join(parts)

    @staticmethod
    def _canonical_issue(canonical_href: str) -> SEOIssueData | None:
        if not canonical_href:
            return SEOIssueData(
                severity="medium",
                title="Отсутствует canonical",
                description="На странице не найден тег canonical.",
                recommendation="Добавить тег <link rel='canonical'> с каноническим URL."
            )

        parsed = urlparse(canonical_href)
        lowered_href = canonical_href.lower()

        if lowered_href.startswith(("javascript:", "mailto:", "tel:")):
            return SEOIssueData(
                severity="high",
                title="Некорректный canonical",
                description="Canonical содержит недопустимую ссылку.",
                recommendation="Указать корректный HTTP(S) URL или абсолютный/относительный путь страницы."
            )

        if canonical_href.startswith("#") or parsed.fragment:
            return SEOIssueData(
                severity="medium",
                title="Canonical содержит фрагмент",
                description="Canonical не должен содержать якорь или ссылку только на фрагмент.",
                recommendation="Использовать canonical без символа # и фрагментов URL."
            )

        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            return SEOIssueData(
                severity="medium",
                title="Нестандартная схема canonical",
                description=f"Canonical использует схему '{parsed.scheme}'.",
                recommendation="Использовать canonical со схемой http/https."
            )

        return None

    def analyze(self, html: str) -> SEOAnalysisResult:
        soup = BeautifulSoup(html, "html.parser")

        issues: list[SEOIssueData] = []
        metrics: list[tuple[str, float, str | None]] = []

        title_tag = soup.title
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        title_length = len(title_text)
        metrics.append(("title_length", float(title_length), "chars"))

        if not title_tag or not title_text:
            issues.append(
                SEOIssueData(
                    severity="high",
                    title="Отсутствует тег title",
                    description="На странице отсутствует тег <title> или он пустой.",
                    recommendation="Добавить уникальный и информативный title длиной 30–60 символов."
                )
            )
        elif title_length < 30:
            issues.append(
                SEOIssueData(
                    severity="medium",
                    title="Слишком короткий title",
                    description=f"Длина title составляет {title_length} символов.",
                    recommendation="Увеличить длину title до 30–60 символов."
                )
            )
        elif title_length > 60:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Слишком длинный title",
                    description=f"Длина title составляет {title_length} символов.",
                    recommendation="Сократить title до 30–60 символов."
                )
            )

        description_content = self._get_meta_content(soup, "description")

        description_length = len(description_content)
        metrics.append(("meta_description_length", float(description_length), "chars"))

        if not description_content:
            issues.append(
                SEOIssueData(
                    severity="high",
                    title="Отсутствует meta description",
                    description="На странице отсутствует meta description или он пустой.",
                    recommendation="Добавить meta description длиной примерно 120–160 символов."
                )
            )
        elif description_length < 120:
            issues.append(
                SEOIssueData(
                    severity="medium",
                    title="Слишком короткий meta description",
                    description=f"Длина meta description составляет {description_length} символов.",
                    recommendation="Увеличить описание до 120–160 символов."
                )
            )
        elif description_length > 160:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Слишком длинный meta description",
                    description=f"Длина meta description составляет {description_length} символов.",
                    recommendation="Сократить описание до 120–160 символов."
                )
            )

        h1_tags = soup.find_all("h1")
        h1_count = len(h1_tags)
        metrics.append(("h1_count", float(h1_count), None))

        h2_count = len(soup.find_all("h2"))
        h3_count = len(soup.find_all("h3"))
        metrics.append(("h2_count", float(h2_count), None))
        metrics.append(("h3_count", float(h3_count), None))

        if h1_count == 0:
            issues.append(
                SEOIssueData(
                    severity="high",
                    title="Отсутствует H1",
                    description="На странице не найдено ни одного тега <h1>.",
                    recommendation="Добавить один основной заголовок H1."
                )
            )
        elif h1_count > 1:
            issues.append(
                SEOIssueData(
                    severity="medium",
                    title="Несколько H1 на странице",
                    description=f"На странице найдено {h1_count} тегов <h1>.",
                    recommendation="Оставить один основной H1."
                )
            )

        headings = soup.find_all(re.compile(r"^h[1-6]$"))
        heading_level_skips = 0
        previous_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if previous_level and level - previous_level > 1:
                heading_level_skips += 1
            previous_level = level
        metrics.append(("heading_level_skips", float(heading_level_skips), None))

        if heading_level_skips > 0:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Нарушена последовательность заголовков",
                    description=f"Найдено {heading_level_skips} переходов через уровень заголовка.",
                    recommendation="Стараться выстраивать структуру заголовков последовательно, без пропуска уровней."
                )
            )

        if h1_count == 1 and h2_count == 0 and h3_count > 0:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Есть H3 без H2",
                    description="На странице есть подзаголовки H3, но не найдено ни одного H2.",
                    recommendation="Проверить иерархию заголовков и при необходимости добавить H2."
                )
            )

        canonical_tag = soup.find(lambda tag: self._link_rel_contains(tag, "canonical"))
        canonical_href = canonical_tag.get("href", "").strip() if canonical_tag else ""
        metrics.append(("seo_has_canonical", 1.0 if canonical_href else 0.0, None))
        metrics.append(("canonical_is_absolute", 1.0 if urlparse(canonical_href).scheme in {"http", "https"} else 0.0, None))

        canonical_issue = self._canonical_issue(canonical_href)
        if canonical_issue:
            issues.append(canonical_issue)

        robots_content = self._get_meta_content(soup, "robots")
        metrics.append(("has_robots_meta", 1.0 if robots_content else 0.0, None))

        if not robots_content:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Отсутствует meta robots",
                    description="На странице отсутствует meta robots.",
                    recommendation="Добавить meta robots, если для страницы важны правила индексации."
                )
            )

        meta_keywords = self._get_meta_content(soup, "keywords")
        metrics.append(("has_meta_keywords", 1.0 if meta_keywords else 0.0, None))

        if not meta_keywords:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Отсутствует meta keywords",
                    description="Meta keywords не найден.",
                    recommendation="При необходимости можно добавить keywords для внутренних процессов, но для SEO это вторичный сигнал."
                )
            )

        html_tag = soup.find("html")
        lang_value = (html_tag.get("lang") or "").strip() if html_tag else ""
        metrics.append(("has_lang", 1.0 if lang_value else 0.0, None))

        if not lang_value:
            issues.append(
                SEOIssueData(
                    severity="medium",
                    title="Отсутствует lang у HTML",
                    description="У тега <html> не задан атрибут lang.",
                    recommendation="Указать основной язык страницы, например <html lang='ru'>."
                )
            )

        favicon_tag = soup.find(lambda tag: self._link_rel_contains(tag, "icon"))
        favicon_href = (favicon_tag.get("href") or "").strip() if favicon_tag else ""
        metrics.append(("has_favicon", 1.0 if favicon_href else 0.0, None))

        if not favicon_href:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Не найден favicon",
                    description="На странице отсутствует ссылка на favicon.",
                    recommendation="Добавить <link rel='icon'> или аналогичный тег для иконки сайта."
                )
            )

        og_title = self._get_property_content(soup, "og:title")
        og_description = self._get_property_content(soup, "og:description")
        og_image = self._get_property_content(soup, "og:image")
        og_url = self._get_property_content(soup, "og:url")
        og_type = self._get_property_content(soup, "og:type")
        og_count = sum(1 for value in [og_title, og_description, og_image, og_url, og_type] if value)
        metrics.append(("open_graph_basic_count", float(og_count), None))
        metrics.append(("has_open_graph_basics", 1.0 if og_count >= 3 else 0.0, None))

        if og_count == 0:
            issues.append(
                SEOIssueData(
                    severity="medium",
                    title="Отсутствуют Open Graph метатеги",
                    description="Не найдены базовые Open Graph поля для превью в соцсетях.",
                    recommendation="Добавить как минимум og:title, og:description и og:image."
                )
            )
        elif og_count < 3:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Open Graph заполнен частично",
                    description=f"Найдено только {og_count} базовых Open Graph полей.",
                    recommendation="Дополнить Open Graph ключевыми полями: og:title, og:description, og:image, og:url, og:type."
                )
            )

        structured_data_scripts = 0
        for script_tag in soup.find_all("script"):
            script_type = (script_tag.get("type") or "").strip().lower()
            script_content = script_tag.get_text(strip=True)
            if script_type == "application/ld+json" and script_content:
                structured_data_scripts += 1
        microdata_items = len(soup.find_all(attrs={"itemscope": True}))
        structured_data_count = structured_data_scripts + microdata_items
        metrics.append(("structured_data_count", float(structured_data_count), None))
        metrics.append(("has_structured_data", 1.0 if structured_data_count > 0 else 0.0, None))

        if structured_data_count == 0:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Не найдены структурированные данные",
                    description="На странице не обнаружены JSON-LD или microdata-разметка.",
                    recommendation="Добавить структурированные данные там, где это уместно для типа страницы."
                )
            )

        anchors = soup.find_all("a")
        internal_links = 0
        external_links = 0
        empty_anchor_count = 0
        duplicate_anchor_count = 0
        seen_anchor_targets: set[tuple[str, str]] = set()

        for anchor in anchors:
            href = (anchor.get("href") or "").strip()
            anchor_text = anchor.get_text(" ", strip=True)
            normalized_text = re.sub(r"\s+", " ", anchor_text)

            if not href or (not normalized_text and not anchor.find("img", alt=True)):
                empty_anchor_count += 1

            if href:
                duplicate_key = (href, normalized_text)
                if duplicate_key in seen_anchor_targets:
                    duplicate_anchor_count += 1
                else:
                    seen_anchor_targets.add(duplicate_key)

            if self._is_internal_href(href):
                internal_links += 1
            elif self._is_external_href(href):
                external_links += 1

        metrics.append(("seo_internal_links_count", float(internal_links), None))
        metrics.append(("seo_external_links_count", float(external_links), None))
        metrics.append(("empty_anchors_count", float(empty_anchor_count), None))
        metrics.append(("duplicate_anchors_count", float(duplicate_anchor_count), None))

        if empty_anchor_count > 0:
            issues.append(
                SEOIssueData(
                    severity="medium" if empty_anchor_count >= 3 else "low",
                    title="Найдены пустые ссылки",
                    description=f"Обнаружено {empty_anchor_count} ссылок без href и/или без понятного содержимого.",
                    recommendation="Заполнить href и добавить понятный текст или alt у изображения внутри ссылки."
                )
            )

        if duplicate_anchor_count > 0:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Есть повторяющиеся ссылки",
                    description=f"Найдено {duplicate_anchor_count} повторов ссылок с одинаковым href и текстом.",
                    recommendation="Проверить, не создают ли повторяющиеся ссылки избыточную навигацию."
                )
            )

        images = soup.find_all("img")
        total_images = len(images)
        images_without_alt = sum(1 for img in images if not (img.get("alt") or "").strip())
        lazy_loaded_images = sum(1 for img in images if (img.get("loading") or "").strip().lower() == "lazy")

        metrics.append(("images_count", float(total_images), None))
        metrics.append(("images_without_alt", float(images_without_alt), None))
        metrics.append(("images_lazy_loaded", float(lazy_loaded_images), None))
        metrics.append((
            "images_lazy_loaded_ratio",
            float((lazy_loaded_images / total_images) * 100) if total_images else 0.0,
            "percent",
        ))

        if total_images > 0 and images_without_alt > 0:
            severity = "medium" if images_without_alt >= 3 else "low"
            issues.append(
                SEOIssueData(
                    severity=severity,
                    title="Изображения без alt",
                    description=(
                        f"Найдено {images_without_alt} изображений без заполненного атрибута alt "
                        f"из {total_images}."
                    ),
                    recommendation="Добавить осмысленные атрибуты alt ко всем важным изображениям."
                )
            )

        if total_images >= 3 and lazy_loaded_images == 0:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Изображения не используют lazy loading",
                    description="На странице несколько изображений, но не найден loading='lazy'.",
                    recommendation="Для некритичных изображений ниже первого экрана рассмотреть loading='lazy'."
                )
            )

        visible_text = self._extract_visible_text(soup)
        text_length = len(visible_text)
        html_length = len(html)
        text_to_html_ratio = (text_length / html_length) * 100 if html_length else 0.0

        metrics.append(("text_length", float(text_length), "chars"))
        metrics.append(("text_to_html_ratio", float(text_to_html_ratio), "percent"))

        if text_length < 300:
            issues.append(
                SEOIssueData(
                    severity="medium",
                    title="Мало текстового контента",
                    description=f"Объем видимого текста составляет {text_length} символов.",
                    recommendation="Добавить больше уникального и полезного текстового контента, если это соответствует типу страницы."
                )
            )

        if html_length >= 1000 and text_to_html_ratio < 10:
            issues.append(
                SEOIssueData(
                    severity="low",
                    title="Низкое соотношение текста к HTML",
                    description=f"Соотношение текста к HTML составляет {text_to_html_ratio:.1f}%.",
                    recommendation="Проверить, не перегружена ли страница служебной разметкой и достаточно ли на ней полезного текста."
                )
            )

        return SEOAnalysisResult(metrics=metrics, issues=issues)

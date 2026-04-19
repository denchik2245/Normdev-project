from dataclasses import dataclass

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

        description_tag = soup.find("meta", attrs={"name": "description"})
        description_content = ""
        if description_tag and description_tag.get("content"):
            description_content = description_tag.get("content").strip()

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

        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        canonical_href = canonical_tag.get("href", "").strip() if canonical_tag else ""
        metrics.append(("has_canonical", 1.0 if canonical_href else 0.0, None))

        if not canonical_href:
            issues.append(
                SEOIssueData(
                    severity="medium",
                    title="Отсутствует canonical",
                    description="На странице не найден тег canonical.",
                    recommendation="Добавить тег <link rel='canonical'> с каноническим URL."
                )
            )

        robots_tag = soup.find("meta", attrs={"name": "robots"})
        robots_content = robots_tag.get("content", "").strip() if robots_tag else ""
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

        images = soup.find_all("img")
        total_images = len(images)
        images_without_alt = sum(1 for img in images if not (img.get("alt") or "").strip())

        metrics.append(("images_count", float(total_images), None))
        metrics.append(("images_without_alt", float(images_without_alt), None))

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

        return SEOAnalysisResult(metrics=metrics, issues=issues)
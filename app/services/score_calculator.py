from app.utils.helpers import calculate_category_score


class ScoreCalculator:
    def calculate(
        self,
        status_code: int,
        is_https: bool,
        seo_issues: list,
        technical_issues: list,
        performance_issues: list
    ) -> float:
        seo_score = calculate_category_score(seo_issues)
        technical_score = calculate_category_score(technical_issues)
        performance_score = calculate_category_score(performance_issues)

        total_score = (
            seo_score * 0.35
            + technical_score * 0.40
            + performance_score * 0.25
        )

        if status_code >= 500:
            total_score -= 35
        elif status_code >= 400:
            total_score -= 25
        elif status_code >= 300:
            total_score -= 8

        if not is_https:
            total_score -= 8

        if total_score < 0:
            total_score = 0.0

        return round(total_score, 2)

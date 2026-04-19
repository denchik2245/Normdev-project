class ScoreCalculator:
    def calculate(
        self,
        status_code: int,
        is_https: bool,
        seo_issues: list,
        technical_issues: list,
        performance_issues: list
    ) -> float:
        total_score = 100.0

        if status_code >= 500:
            total_score -= 50
        elif status_code >= 400:
            total_score -= 40
        elif status_code >= 300:
            total_score -= 10

        if not is_https:
            total_score -= 10

        all_issues = seo_issues + technical_issues + performance_issues

        for issue in all_issues:
            if issue.severity == "high":
                total_score -= 10
            elif issue.severity == "medium":
                total_score -= 5
            elif issue.severity == "low":
                total_score -= 2

        if total_score < 0:
            total_score = 0.0

        return round(total_score, 2)
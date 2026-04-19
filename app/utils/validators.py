def normalize_url(url: str) -> str:
    url = (url or "").strip()

    if not url:
        return ""

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    return url
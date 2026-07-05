from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))

    if not results:
        return "No search results found."

    formatted = []
    for r in results:
        formatted.append(
            f"Title: {r.get('title', '')}\nURL: {r.get('href', '')}\nSnippet: {r.get('body', '')}"
        )

    return "\n\n".join(formatted)

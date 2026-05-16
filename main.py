import asyncio
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

GARUDA_BASE_URL = "https://garuda.kemdiktisaintek.go.id"

mcp = FastMCP(
    "garuda",
    dependencies=[
        "beautifulsoup4",
        "httpx",
        "lxml",
    ],
)


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def extract_garuda_id_from_url(url: str) -> str:
    match = re.search(r"/documents/detail/(\d+)", url)
    return match.group(1) if match else ""


def build_garuda_detail_url(garuda_id_or_url: str) -> str:
    garuda_id_or_url = clean_text(garuda_id_or_url)
    if garuda_id_or_url.startswith("http://") or garuda_id_or_url.startswith("https://"):
        return garuda_id_or_url
    return f"{GARUDA_BASE_URL}/documents/detail/{garuda_id_or_url}"


def format_simple_apa_citation(article: dict[str, Any]) -> str:
    authors = article.get("authors", [])
    journal = article.get("journal") or "Unknown journal"
    title = article.get("title") or "Untitled"
    doi = article.get("doi")
    detail_url = article.get("detail_url")

    if authors:
        author_text = ", ".join(authors[:5])
        if len(authors) > 5:
            author_text += ", et al."
    else:
        author_text = "Unknown author"

    citation = f"{author_text}. {title}. {journal}."
    if doi:
        citation += f" DOI: {doi}."
    elif detail_url:
        citation += f" {detail_url}"
    return citation.strip()


def parse_garuda_article_item(item, base_url: str = GARUDA_BASE_URL) -> dict[str, Any]:
    title_tag = item.select_one("a.title-article")
    title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else ""
    detail_url = urljoin(base_url, title_tag.get("href", "")) if title_tag else ""
    garuda_id = extract_garuda_id_from_url(detail_url)

    authors = [
        clean_text(author.get_text(" ", strip=True))
        for author in item.select("a.author-article")
    ]

    subtitles = item.select("xmp.subtitle-article")
    journal = clean_text(subtitles[0].get_text(" ", strip=True)) if len(subtitles) > 0 else ""
    publisher = clean_text(subtitles[1].get_text(" ", strip=True)) if len(subtitles) > 1 else ""

    abstract_tag = item.select_one(".abstract-article xmp.abstract-article")
    abstract = clean_text(abstract_tag.get_text(" ", strip=True)) if abstract_tag else ""

    links = item.select("p.action-article a")
    download_original = ""
    original_source = ""
    google_scholar = ""
    full_pdf = ""
    doi = ""

    for link in links:
        text = clean_text(link.get_text(" ", strip=True))
        href = link.get("href", "")

        if "Download Original" in text:
            download_original = href
        elif "Original Source" in text:
            original_source = href
        elif "Check in Google Scholar" in text:
            google_scholar = href
        elif "Full PDF" in text:
            full_pdf = href
        elif "DOI:" in text:
            doi = text.replace("DOI:", "").strip()

    article = {
        "garuda_id": garuda_id,
        "title": title,
        "authors": authors,
        "authors_text": "; ".join(authors),
        "journal": journal,
        "publisher": publisher,
        "abstract": abstract,
        "doi": doi,
        "detail_url": detail_url,
        "download_original": download_original,
        "original_source": original_source,
        "full_pdf": full_pdf,
        "google_scholar": google_scholar,
    }
    article["citation"] = format_simple_apa_citation(article)
    return article


def parse_garuda_search_page(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")

    found_header = soup.select_one("h2.ui.header")
    found_text = clean_text(found_header.get_text(" ", strip=True)) if found_header else ""
    total_documents = None

    match = re.search(r"Found\s+([\d,\.]+)\s+documents", found_text)
    if match:
        total_documents = int(match.group(1).replace(",", "").replace(".", ""))

    articles = [
        parse_garuda_article_item(item)
        for item in soup.select("div.article-item")
    ]

    return {
        "total_documents": total_documents,
        "articles": articles,
        "articles_on_page": len(articles),
    }


def parse_garuda_detail_page(html: str, detail_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")

    article_display = soup.select_one("div.article-display")
    if article_display is None:
        return {
            "garuda_id": extract_garuda_id_from_url(detail_url),
            "detail_url": detail_url,
            "title": "",
            "journal_short": "",
            "journal_volume": "",
            "authors": [],
            "publish_date": "",
            "abstract": "",
            "copyright": "",
            "download_original": "",
            "google_scholar": "",
            "citation": "",
        }

    container = article_display.find("div")
    journal_blocks = container.select("xmp") if container else []
    journal_short = clean_text(journal_blocks[0].get_text(" ", strip=True)) if len(journal_blocks) > 0 else ""
    journal_volume = clean_text(journal_blocks[1].get_text(" ", strip=True)) if len(journal_blocks) > 1 else ""

    title_tag = article_display.select_one("h3.ui.header xmp")
    title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else ""

    authors = [
        clean_text(author.get_text(" ", strip=True))
        for author in article_display.select("a[href*='/author/view/'] xmp")
    ]

    publish_date = ""
    article_info = article_display.select_one("div.four.wide.column")
    if article_info:
        info_text = clean_text(article_info.get_text(" ", strip=True))
        match = re.search(r"Publish Date\s+(.*)", info_text)
        if match:
            publish_date = clean_text(match.group(1))

    abstract_tag = article_display.select_one("xmp.abstract-article")
    abstract = clean_text(abstract_tag.get_text(" ", strip=True)) if abstract_tag else ""

    download_original = ""
    google_scholar = ""
    original_source = ""
    full_pdf = ""
    doi = ""

    for link in soup.select("a[href]"):
        text = clean_text(link.get_text(" ", strip=True))
        href = link.get("href", "")
        if "Download Original" in text:
            download_original = href
        elif "Check in Google Scholar" in text or "Google Scholar" in text:
            google_scholar = href
        elif "Original Source" in text:
            original_source = href
        elif "Full PDF" in text:
            full_pdf = href
        elif "DOI:" in text:
            doi = text.replace("DOI:", "").strip()

    copyright_text = ""
    paragraphs = article_display.select("div.art-content p")
    if paragraphs:
        copyright_text = clean_text(paragraphs[-1].get_text(" ", strip=True))

    article = {
        "garuda_id": extract_garuda_id_from_url(detail_url),
        "detail_url": detail_url,
        "title": title,
        "journal_short": journal_short,
        "journal_volume": journal_volume,
        "journal": clean_text(f"{journal_short} {journal_volume}"),
        "authors": authors,
        "authors_text": "; ".join(authors),
        "publish_date": publish_date,
        "abstract": abstract,
        "copyright": copyright_text,
        "doi": doi,
        "download_original": download_original,
        "original_source": original_source,
        "full_pdf": full_pdf,
        "google_scholar": google_scholar,
    }
    article["citation"] = format_simple_apa_citation(article)
    return article


async def fetch_garuda_search_page(
    client: httpx.AsyncClient,
    query: str,
    page: int = 1,
) -> str:
    response = await client.get(
        f"{GARUDA_BASE_URL}/documents",
        params={
            "q": query,
            "page": page,
        },
    )
    response.raise_for_status()
    return response.text


async def fetch_garuda_detail_page(
    client: httpx.AsyncClient,
    garuda_id_or_url: str,
) -> tuple[str, str]:
    detail_url = build_garuda_detail_url(garuda_id_or_url)
    response = await client.get(detail_url)
    response.raise_for_status()
    return response.text, str(response.url)


@mcp.tool()
async def search_garuda(
    query: str,
    limit: int = 10,
    max_pages: int = 3,
    include_abstract: bool = True,
    delay_seconds: float = 0.5,
) -> dict[str, Any]:
    """
    Search Indonesian local journals and articles from GARUDA.

    Args:
        query: Search query
        limit: Maximum number of results to return
        max_pages: Maximum number of result pages to scan
        include_abstract: Whether to include abstract text in the output
        delay_seconds: Delay between page requests to stay polite to the site

    Returns:
        Matching GARUDA articles with citation-ready metadata
    """
    limit = max(1, min(limit, 50))
    max_pages = max(1, min(max_pages, 10))
    delay_seconds = max(0.0, min(delay_seconds, 5.0))

    headers = {
        "User-Agent": "Mozilla/5.0 mcp-garuda/0.1",
        "Accept": "text/html,application/xhtml+xml",
    }

    collected_articles = []
    total_documents = None

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30,
        follow_redirects=True,
    ) as client:
        for page in range(1, max_pages + 1):
            html = await fetch_garuda_search_page(client, query=query, page=page)
            parsed = parse_garuda_search_page(html)

            if total_documents is None:
                total_documents = parsed["total_documents"]

            for article in parsed["articles"]:
                if not include_abstract:
                    article["abstract"] = ""
                collected_articles.append(article)
                if len(collected_articles) >= limit:
                    break

            if len(collected_articles) >= limit or parsed["articles_on_page"] == 0:
                break

            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

    return {
        "query": query,
        "source": "GARUDA",
        "source_url": GARUDA_BASE_URL,
        "total_documents": total_documents,
        "returned_results": len(collected_articles),
        "results": collected_articles,
    }


@mcp.tool()
async def get_garuda_detail(
    garuda_id_or_url: str,
) -> dict[str, Any]:
    """
    Fetch the detail page for a GARUDA article by article id or detail URL.

    Args:
        garuda_id_or_url: Numeric GARUDA article id or full GARUDA detail URL

    Returns:
        Detailed GARUDA article metadata from the article page
    """
    headers = {
        "User-Agent": "Mozilla/5.0 mcp-garuda/0.1",
        "Accept": "text/html,application/xhtml+xml",
    }

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30,
        follow_redirects=True,
    ) as client:
        html, resolved_url = await fetch_garuda_detail_page(client, garuda_id_or_url)

    return parse_garuda_detail_page(html, resolved_url)


if __name__ == "__main__":
    mcp.run()

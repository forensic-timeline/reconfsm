"""
Web Activity Extraction Script

A unified web activity extractor that works with both Firefox and Chrome history entries.
This script extracts meaningful information about web activities including:
- Downloads
- Searches
- General web access
"""

import re
from urllib.parse import urlparse, parse_qs, unquote


def web_activity(row):
    if row.get('source') not in ['WEBHIST']:
        return None

    source_long = row.get('source_long', '')
    if 'firefox history' not in source_long.lower():
        return None

    message = row.get('message', '')
    if not message:
        return None

    download_result = _extract_download_info(message)
    if download_result:
        return download_result

    search_result = _extract_search_info(message)
    if search_result:
        return search_result

    web_access_result = _extract_web_access_info(message)
    if web_access_result:
        return web_access_result

    return None


def _extract_web_access_info(message):
    """
    Patterns:
    - "Transition: TYPED"
    - "Transition: LINK"
    - "Transition: REDIRECT"
    """

    if re.search(r'Transition: TYPED', message):
        site_name = _util_site_name(message)
        if site_name:
            return f'Web : {site_name}', "accessed_website_direct", None

    if re.search(r'Transition: LINK', message):
        site_name = _util_site_name(message)
        if site_name:
            return f'Web : {site_name}', "accessed_website_link", None

    if re.search(r'Transition: REDIRECT', message):
        site_name = _util_site_name(message)
        if site_name:
            return f'Web : {site_name}', "accessed_website_redirect", None

    return None


def _extract_download_info(message):
    """
    Pattern: "Transition: DOWNLOAD"
    """
    download_pattern = r'Transition: DOWNLOAD'
    match = re.search(download_pattern, message)

    if match:
        download_data = re.search(r'https?://[^\s]+\s+\(([^)]+)\)', message)
        download_file = download_data.group(1)
        download_file = unquote(download_file)
        download_file = re.sub(r'[^\w\.-]', '_', download_file)

        return f'File: {download_file}', "downloaded_file", None

    return None


def _extract_search_info(message):
    """
    Pattern (AND):
    - search?q= / search?p= / &q= / ?q= (search patterns)
    """

    search_pattern = r'^(https?:\/\/[^\s]*?(search\?[qp]=|[?&][q]=))'
    if re.search(search_pattern, message):
        search_query = _util_search_query(message)
        if search_query:
            return f'Search Engine {search_query}', "performed_search", None

    return None


def _util_search_query(message):

    url_match = re.search(r'(https?://[^\s)]+)', message)
    if not url_match:
        return _util_name_from_parentheses(message)

    url = url_match.group(1)

    host_match = re.search(r'Host:\s+([^\s]+)', message)
    if host_match:
        host = host_match.group(1).lower()
        if host.startswith('www.'):
            host = host[4:]
        search_engine = '.'.join(host.split('.')[:-1])

    else:
        search_engine = 'unknown'

    query_text = None
    query_patterns = [
        r'[?&][qp]=([^&]+)',
        r'[?&]t=[^&]*&q=([^&]+)'
    ]

    for pattern in query_patterns:
        match = re.search(pattern, url)
        if match:
            query_text = match.group(1)
            break

    if query_text:

        query_text = unquote(query_text)
        query_text = query_text.replace('+', ' ')
        query_text = re.sub(r'[^\w\s.,?!-]', '', query_text)
        query_text = ' '.join(query_text.split())

        if query_text:
            return f"{search_engine}: {query_text}"

    return _util_name_from_parentheses(message)


def _util_name_from_parentheses(message):
    """
    Fallback method: extract text from the first parentheses in the message
    """
    paren_match = re.search(r'\(([^)]+)\)', message)
    if paren_match:
        text = paren_match.group(1)

        text = re.sub(r'[^\w\s.,?!-]', '', text)
        text = ' '.join(text.split())

        if text and len(text) > 0:
            return text

    return None


def _util_site_name(message):

    url_match = re.search(r'(https?://[^\s)]+)', message)
    if not url_match:
        return None

    url = url_match.group(1)
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path

    if domain.startswith('www.'):
        domain = domain[4:]

    path_segments = [segment for segment in path.split('/') if segment]
    path_segments = path_segments[:3]

    if path_segments:
        state = f"{domain}/{'/'.join(path_segments)}"
    else:
        state = domain

    return state

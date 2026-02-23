"""
Unit Tests for Web Activity Extractor

This module contains comprehensive unit tests for the web_activity.py script,
testing various web activity patterns including downloads, searches, and web access.

Usage:
    pytest tests/test_web_activity.py -v
    python -m unittest tests/test_web_activity.py
"""

import pytest
from reconfsm.converter.scripts.web_activity import (
    web_activity,
    _extract_download_info,
    _extract_search_info,
    _extract_web_access_info,
    _util_search_query,
    _util_site_name,
    _util_name_from_parentheses,
)


# ---------------------------------------------------------------------------
# Fixtures – reusable base rows
# ---------------------------------------------------------------------------

@pytest.fixture
def base_firefox_row():
    """Minimal valid Firefox history row."""
    return {
        "source": "WEBHIST",
        "source_long": "Firefox History",
        "message": "",
    }


# ===========================================================================
# web_activity() – top-level dispatcher
# ===========================================================================

class TestWebActivity:
    """Tests for the main web_activity() dispatcher."""

    # --- source / source_long filtering ---

    def test_returns_none_for_non_webhist_source(self, base_firefox_row):
        base_firefox_row["source"] = "SYSLOG"
        assert web_activity(base_firefox_row) is None

    def test_returns_none_when_source_key_missing(self, base_firefox_row):
        del base_firefox_row["source"]
        assert web_activity(base_firefox_row) is None

    def test_returns_none_for_non_firefox_source_long(self, base_firefox_row):
        base_firefox_row["source_long"] = "Chrome History"
        base_firefox_row["message"] = "https://example.com Transition: TYPED"
        assert web_activity(base_firefox_row) is None

    def test_returns_none_when_source_long_missing(self, base_firefox_row):
        del base_firefox_row["source_long"]
        base_firefox_row["message"] = "https://example.com Transition: TYPED"
        assert web_activity(base_firefox_row) is None

    def test_returns_none_when_message_empty(self, base_firefox_row):
        base_firefox_row["message"] = ""
        assert web_activity(base_firefox_row) is None

    def test_returns_none_when_message_missing(self, base_firefox_row):
        del base_firefox_row["message"]
        assert web_activity(base_firefox_row) is None

    # --- download dispatch ---

    def test_dispatch_to_download(self, base_firefox_row):
        base_firefox_row["message"] = (
            "https://example.com/file.zip (file.zip) Transition: DOWNLOAD"
        )
        result = web_activity(base_firefox_row)
        assert result is not None
        assert result[1] == "downloaded_file"

    # --- search dispatch ---

    def test_dispatch_to_search(self, base_firefox_row):
        base_firefox_row["message"] = (
            "https://www.google.com/search?q=python+forensics "
            "Host: www.google.com Transition: LINK"
        )
        result = web_activity(base_firefox_row)
        assert result is not None
        assert result[1] == "performed_search"

    # --- web access dispatch ---

    def test_dispatch_to_web_access_typed(self, base_firefox_row):
        base_firefox_row["message"] = (
            "https://example.com Transition: TYPED"
        )
        result = web_activity(base_firefox_row)
        assert result is not None
        assert result[1] == "accessed_website_direct"

    # --- returns None when no pattern matches ---

    def test_returns_none_for_unrecognised_message(self, base_firefox_row):
        base_firefox_row["message"] = "Some random log line with no pattern"
        assert web_activity(base_firefox_row) is None

    # --- case-insensitive source_long matching ---

    def test_source_long_case_insensitive(self, base_firefox_row):
        base_firefox_row["source_long"] = "FIREFOX HISTORY"
        base_firefox_row["message"] = "https://example.com Transition: TYPED"
        result = web_activity(base_firefox_row)
        assert result is not None


# ===========================================================================
# _extract_download_info()
# ===========================================================================

class TestExtractDownloadInfo:
    """Tests for _extract_download_info()."""

    def test_basic_download(self):
        message = "https://example.com/file.zip (file.zip) Transition: DOWNLOAD"
        result = _extract_download_info(message)
        assert result is not None
        label, activity, extra = result
        assert activity == "downloaded_file"
        assert label == "File: file.zip"
        assert extra is None

    def test_download_url_encoded_filename(self):
        message = (
            "https://example.com/My%20File.pdf (My%20File.pdf) Transition: DOWNLOAD"
        )
        result = _extract_download_info(message)
        assert result is not None
        label, activity, _ = result
        # Should URL-decode the filename
        assert "My_File.pdf" in label or "My File.pdf" in label

    def test_no_download_transition_returns_none(self):
        message = "https://example.com Transition: TYPED"
        assert _extract_download_info(message) is None

    def test_empty_message_returns_none(self):
        assert _extract_download_info("") is None

    def test_download_label_starts_with_file(self):
        message = "https://example.com/report.pdf (report.pdf) Transition: DOWNLOAD"
        result = _extract_download_info(message)
        assert result[0].startswith("File:")

    def test_download_third_element_is_none(self):
        message = "https://example.com/data.csv (data.csv) Transition: DOWNLOAD"
        result = _extract_download_info(message)
        assert result[2] is None


# ===========================================================================
# _extract_search_info()
# ===========================================================================


class TestExtractSearchInfo:
    """Tests for _extract_search_info() using parametrization."""

    @pytest.mark.parametrize("message, expected_query", [
        (
            "https://www.google.com/search?q=python+forensics Host: www.google.com",
            "python forensics"
        ),
        (
            "https://search.yahoo.com/search?p=malware+analysis Host: search.yahoo.com",
            "malware analysis"
        ),
        (
            "https://duckduckgo.com/?t=ffab&q=linux+commands Host: duckduckgo.com",
            "linux commands"
        ),
    ])
    def test_valid_search_extraction(self, message, expected_query):
        result = _extract_search_info(message)
        assert result is not None
        label, activity, extra = result
        assert activity == "performed_search"
        assert expected_query in label.lower()
        assert label.startswith("Search Engine")
        assert extra is None

    @pytest.mark.parametrize("invalid_message", [
        "https://example.com/about Transition: TYPED",
        "",
        "Just some random log text with no URL",        
    ])
    def test_invalid_search_returns_none(self, invalid_message):
        assert _extract_search_info(invalid_message) is None


# ===========================================================================
# _extract_web_access_info()
# ===========================================================================

class TestExtractWebAccessInfo:
    """Tests for _extract_web_access_info()."""

    def test_typed_transition(self):
        message = "https://example.com Transition: TYPED"
        result = _extract_web_access_info(message)
        assert result is not None
        label, activity, extra = result
        assert activity == "accessed_website_direct"
        assert "example.com" in label
        assert extra is None

    def test_link_transition(self):
        message = "https://example.com/page Transition: LINK"
        result = _extract_web_access_info(message)
        assert result is not None
        assert result[1] == "accessed_website_link"

    def test_redirect_transition(self):
        message = "https://redirect.example.com/dest Transition: REDIRECT"
        result = _extract_web_access_info(message)
        assert result is not None
        assert result[1] == "accessed_website_redirect"

    def test_no_transition_returns_none(self):
        message = "https://example.com some other text"
        assert _extract_web_access_info(message) is None

    def test_empty_message_returns_none(self):
        assert _extract_web_access_info("") is None

    def test_label_starts_with_web(self):
        message = "https://example.com Transition: TYPED"
        result = _extract_web_access_info(message)
        assert result[0].startswith("Web :")

    def test_www_stripped_from_domain(self):
        message = "https://www.github.com Transition: TYPED"
        result = _extract_web_access_info(message)
        assert result is not None
        assert "www." not in result[0]

    def test_path_included_in_label(self):
        message = "https://example.com/a/b/c/d Transition: TYPED"
        result = _extract_web_access_info(message)
        assert result is not None
        # Only first 3 path segments should be included
        label = result[0]
        assert "a" in label and "b" in label and "c" in label
        assert "d" not in label  # 4th segment should be truncated

    def test_download_transition_NOT_matched(self):
        """DOWNLOAD should not be caught by web access extractor."""
        message = "https://example.com/f.zip (f.zip) Transition: DOWNLOAD"
        assert _extract_web_access_info(message) is None


# ===========================================================================
# _util_site_name()
# ===========================================================================

class TestUtilSiteName:
    """Tests for the _util_site_name() helper."""

    def test_basic_domain(self):
        assert _util_site_name("https://example.com Transition: TYPED") == "example.com"

    def test_www_prefix_removed(self):
        result = _util_site_name("https://www.example.com Transition: TYPED")
        assert result == "example.com"

    def test_domain_with_path(self):
        result = _util_site_name("https://example.com/foo/bar Transition: TYPED")
        assert result == "example.com/foo/bar"

    def test_path_capped_at_three_segments(self):
        result = _util_site_name("https://example.com/a/b/c/d Transition: TYPED")
        assert result == "example.com/a/b/c"
        assert "d" not in result

    def test_no_url_returns_none(self):
        assert _util_site_name("No URL here at all") is None

    def test_empty_string_returns_none(self):
        assert _util_site_name("") is None


# ===========================================================================
# _util_search_query()
# ===========================================================================

class TestUtilSearchQuery:
    """Tests for the _util_search_query() helper."""

    def test_google_q_param(self):
        message = (
            "https://www.google.com/search?q=digital+forensics "
            "Host: www.google.com"
        )
        result = _util_search_query(message)
        assert result is not None
        assert "digital forensics" in result.lower()

    def test_search_engine_name_in_result(self):
        message = (
            "https://www.bing.com/search?q=test "
            "Host: www.bing.com"
        )
        result = _util_search_query(message)
        assert result is not None
        assert "bing" in result.lower()

    def test_no_host_header_returns_unknown_engine(self):
        message = "https://www.google.com/search?q=test"
        result = _util_search_query(message)
        assert result is not None
        assert "unknown" in result.lower()

    def test_fallback_to_parentheses_when_no_url(self):
        message = "Some text (fallback name here)"
        result = _util_search_query(message)
        assert result is not None
        assert "fallback name here" in result

    def test_url_encoded_query_decoded(self):
        message = (
            "https://www.google.com/search?q=hello%20world "
            "Host: www.google.com"
        )
        result = _util_search_query(message)
        assert result is not None
        assert "hello world" in result.lower()

    def test_plus_in_query_replaced_with_space(self):
        message = (
            "https://www.google.com/search?q=hello+world "
            "Host: www.google.com"
        )
        result = _util_search_query(message)
        assert result is not None
        assert "hello world" in result.lower()


# ===========================================================================
# _util_name_from_parentheses()
# ===========================================================================

class TestUtilNameFromParentheses:
    """Tests for the _util_name_from_parentheses() fallback helper."""

    def test_extracts_text_from_parentheses(self):
        assert _util_name_from_parentheses("Some text (hello world) more") == "hello world"

    def test_returns_none_when_no_parentheses(self):
        assert _util_name_from_parentheses("No parens here") is None

    def test_returns_none_for_empty_string(self):
        assert _util_name_from_parentheses("") is None

    def test_strips_special_characters(self):
        result = _util_name_from_parentheses("text (hello@world!) extra")
        assert result is not None
        # Special chars except .,?!- should be stripped
        assert "@" not in result

    def test_collapses_whitespace(self):
        result = _util_name_from_parentheses("text (  hello   world  ) extra")
        assert result == "hello world"

    def test_returns_none_for_empty_parentheses(self):
        # After stripping special chars the result might be empty
        result = _util_name_from_parentheses("text () extra")
        assert result is None

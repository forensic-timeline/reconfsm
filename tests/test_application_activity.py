"""
Unit Tests for Application Activity Extractor

This module contains comprehensive unit tests for application_activity.py,
testing systemd journal-based application launch and termination extraction.

Usage:
    pytest tests/test_application_activity.py -v
    python -m unittest tests/test_application_activity.py
"""

import pytest
from reconfsm.converter.scripts.application_activity import (
    application_activity,
    _extract_application_start,
    _extract_application_termination,
    _util_app_name_from_scope,
)


# ---------------------------------------------------------------------------
# Fixtures – reusable base rows
# ---------------------------------------------------------------------------

@pytest.fixture
def base_systemd_row():
    """Minimal valid systemd journal row."""
    return {
        "source": "LOG",
        "source_long": "Systemd Journal",
        "message": "",
    }


# ===========================================================================
# application_activity() – top-level dispatcher
# ===========================================================================

class TestApplicationActivity:
    """Tests for the main application_activity() dispatcher."""

    # --- source filtering ---

    def test_returns_none_for_non_log_source(self, base_systemd_row):
        base_systemd_row["source"] = "WEBHIST"
        base_systemd_row["message"] = "Started snap.firefox.firefox.scope"
        assert application_activity(base_systemd_row) is None

    def test_returns_none_when_source_key_missing(self, base_systemd_row):
        del base_systemd_row["source"]
        assert application_activity(base_systemd_row) is None

    # --- source_long filtering ---

    def test_returns_none_for_non_systemd_source_long(self, base_systemd_row):
        base_systemd_row["source_long"] = "Syslog"
        base_systemd_row["message"] = "Started snap.firefox.firefox.scope"
        assert application_activity(base_systemd_row) is None

    def test_returns_none_when_source_long_missing(self, base_systemd_row):
        del base_systemd_row["source_long"]
        base_systemd_row["message"] = "Started snap.firefox.firefox.scope"
        assert application_activity(base_systemd_row) is None

    def test_source_long_case_insensitive(self, base_systemd_row):
        base_systemd_row["source_long"] = "SYSTEMD JOURNAL"
        base_systemd_row["message"] = "Started snap.firefox.firefox.scope"
        result = application_activity(base_systemd_row)
        assert result is not None

    # --- message filtering ---

    def test_returns_none_when_message_empty(self, base_systemd_row):
        base_systemd_row["message"] = ""
        assert application_activity(base_systemd_row) is None

    def test_returns_none_when_message_missing(self, base_systemd_row):
        del base_systemd_row["message"]
        assert application_activity(base_systemd_row) is None

    def test_returns_none_for_unrecognised_message(self, base_systemd_row):
        base_systemd_row["message"] = "Some random journal log line"
        assert application_activity(base_systemd_row) is None

    # --- dispatch to start ---

    def test_dispatches_to_start_for_snap_app(self, base_systemd_row):
        base_systemd_row["message"] = "Started snap.firefox.firefox.scope"
        result = application_activity(base_systemd_row)
        assert result is not None
        _, activity, _ = result
        assert activity.startswith("launch_")

    def test_dispatches_to_start_for_gnome_app(self, base_systemd_row):
        base_systemd_row["message"] = (
            "Started app-gnome-org.gnome.Nautilus-12345.scope"
        )
        result = application_activity(base_systemd_row)
        assert result is not None
        _, activity, _ = result
        assert activity.startswith("launch_")

    # --- dispatch to termination ---

    def test_dispatches_to_termination_for_snap_app(self, base_systemd_row):
        base_systemd_row["message"] = (
            "snap.firefox.firefox.scope: Consumed 3min 2.154s CPU time"
        )
        result = application_activity(base_systemd_row)
        assert result is not None
        _, activity, _ = result
        assert activity.startswith("close_")

    def test_dispatches_to_termination_for_gnome_app(self, base_systemd_row):
        base_systemd_row["message"] = (
            "app-gnome-org.gnome.Gedit-9876.scope: Consumed 500ms CPU time"
        )
        result = application_activity(base_systemd_row)
        assert result is not None
        _, activity, _ = result
        assert activity.startswith("close_")


# ===========================================================================
# _extract_application_start()
# ===========================================================================

class TestExtractApplicationStart:
    """Tests for _extract_application_start()."""

    def test_snap_app_start(self):
        message = "Started snap.firefox.firefox.scope"
        result = _extract_application_start(message)
        assert result is not None
        app_name, activity, extra = result
        assert app_name == "firefox"
        assert activity == "launch_firefox"
        assert extra is None

    def test_gnome_app_start(self):
        message = "Started app-gnome-org.gnome.Nautilus-12345.scope"
        result = _extract_application_start(message)
        assert result is not None
        app_name, activity, extra = result
        assert app_name == "nautilus"
        assert activity == "launch_nautilus"
        assert extra is None

    def test_snap_thunderbird_start(self):
        message = "Started snap.thunderbird.thunderbird.scope"
        result = _extract_application_start(message)
        assert result is not None
        assert result[0] == "thunderbird"
        assert result[1] == "launch_thunderbird"

    def test_no_started_keyword_returns_none(self):
        message = "snap.firefox.firefox.scope: Consumed 1min CPU time"
        assert _extract_application_start(message) is None

    def test_empty_message_returns_none(self):
        assert _extract_application_start("") is None

    def test_started_without_scope_returns_none(self):
        """'Started' keyword present but no *.scope suffix."""
        message = "Started some-service.service"
        assert _extract_application_start(message) is None

    def test_unrecognised_scope_name_returns_none(self):
        """Scope name that doesn't match snap or gnome pattern."""
        message = "Started unknown-app-format.scope"
        assert _extract_application_start(message) is None

    def test_activity_format_is_launch_prefix(self):
        message = "Started snap.vlc.vlc.scope"
        result = _extract_application_start(message)
        assert result is not None
        assert result[1] == f"launch_{result[0]}"

    def test_third_element_is_none(self):
        message = "Started snap.code.code.scope"
        result = _extract_application_start(message)
        assert result is not None
        assert result[2] is None


# ===========================================================================
# _extract_application_termination()
# ===========================================================================

class TestExtractApplicationTermination:
    """Tests for _extract_application_termination()."""

    def test_snap_app_termination(self):
        message = "snap.firefox.firefox.scope: Consumed 3min 2.154s CPU time"
        result = _extract_application_termination(message)
        assert result is not None
        label, activity, app_name = result
        assert label == "Desktop"
        assert activity == "close_firefox"
        assert app_name == "firefox"

    def test_gnome_app_termination(self):
        message = (
            "app-gnome-org.gnome.Gedit-9876.scope: Consumed 500ms CPU time"
        )
        result = _extract_application_termination(message)
        assert result is not None
        label, activity, app_name = result
        assert label == "Desktop"
        assert activity == "close_gedit"
        assert app_name == "gedit"

    def test_snap_thunderbird_termination(self):
        message = "snap.thunderbird.thunderbird.scope: Consumed 10s CPU time"
        result = _extract_application_termination(message)
        assert result is not None
        assert result[1] == "close_thunderbird"
        assert result[2] == "thunderbird"

    def test_no_consumed_keyword_returns_none(self):
        message = "Started snap.firefox.firefox.scope"
        assert _extract_application_termination(message) is None

    def test_empty_message_returns_none(self):
        assert _extract_application_termination("") is None

    def test_label_is_always_desktop(self):
        message = "snap.vlc.vlc.scope: Consumed 1s CPU time"
        result = _extract_application_termination(message)
        assert result is not None
        assert result[0] == "Desktop"

    def test_activity_format_is_close_prefix(self):
        message = "snap.code.code.scope: Consumed 5min CPU time"
        result = _extract_application_termination(message)
        assert result is not None
        assert result[1] == f"close_{result[2]}"

    def test_unrecognised_scope_name_returns_none(self):
        message = "unknown-format.scope: Consumed 1s CPU time"
        assert _extract_application_termination(message) is None

    def test_consumed_without_cpu_time_returns_none(self):
        """'Consumed' present but 'CPU time' suffix missing."""
        message = "snap.firefox.firefox.scope: Consumed 3min memory"
        assert _extract_application_termination(message) is None


# ===========================================================================
# _util_app_name_from_scope()
# ===========================================================================

class TestUtilAppNameFromScope:
    """Tests for the _util_app_name_from_scope() helper."""

    # --- snap pattern ---

    def test_snap_firefox(self):
        assert _util_app_name_from_scope("snap.firefox.firefox.scope") == "firefox"

    def test_snap_thunderbird(self):
        assert _util_app_name_from_scope("snap.thunderbird.thunderbird.scope") == "thunderbird"

    def test_snap_vlc(self):
        assert _util_app_name_from_scope("snap.vlc.vlc.scope") == "vlc"

    def test_snap_code(self):
        assert _util_app_name_from_scope("snap.code.code.scope") == "code"

    # --- gnome pattern ---

    def test_gnome_nautilus(self):
        result = _util_app_name_from_scope("app-gnome-org.gnome.Nautilus-12345.scope")
        assert result == "nautilus"

    def test_gnome_gedit(self):
        result = _util_app_name_from_scope("app-gnome-org.gnome.Gedit-9876.scope")
        assert result == "gedit"

    def test_gnome_result_is_lowercase(self):
        """GNOME app names should be lowercased."""
        result = _util_app_name_from_scope("app-gnome-org.gnome.TextEditor-1.scope")
        assert result is not None
        assert result == result.lower()

    # --- unrecognised patterns ---

    def test_unrecognised_scope_returns_none(self):
        assert _util_app_name_from_scope("unknown-app.scope") is None

    def test_empty_string_returns_none(self):
        assert _util_app_name_from_scope("") is None

    def test_plain_scope_suffix_returns_none(self):
        assert _util_app_name_from_scope("session-1.scope") is None

    # --- snap takes priority over gnome ---

    def test_snap_pattern_matched_before_gnome(self):
        """If a scope somehow contains both markers, snap wins."""
        scope = "snap.gnome-calculator.gnome.Calculator-1.scope"
        result = _util_app_name_from_scope(scope)
        assert result == "gnome-calculator"

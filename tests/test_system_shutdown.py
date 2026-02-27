"""
Unit Tests for System Shutdown Activity Extractor

This module contains comprehensive unit tests for system_shutdown.py,
testing systemd journal-based scheduled, manual, completed, and forceful
shutdown event extraction.

Usage:
    pytest tests/test_system_shutdown.py -v
    python -m unittest tests/test_system_shutdown.py
"""

import pytest
from reconfsm.converter.scripts.system_shutdown import (
    system_shutdown,
    _extract_scheduled_shutdown,
    _extract_manual_shutdown,
    _extract_shutdown_completion,
    _extract_forceful_shutdown,
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
        "datetime": "2024-06-01T10:00:00Z",
        "message": "",
    }


class TestSystemShutdown:
    """Tests for the system_shutdown() dispatcher."""

    def test_returns_none_for_non_log_source(self, base_systemd_row):
        base_systemd_row["source"] = "WEBHIST"
        base_systemd_row["message"] = "COMMAND=/usr/sbin/poweroff"
        assert system_shutdown(base_systemd_row) is None

    def test_returns_none_when_source_key_missing(self, base_systemd_row):
        del base_systemd_row["source"]
        assert system_shutdown(base_systemd_row) is None

    def test_returns_none_for_non_systemd_source_long(self, base_systemd_row):
        base_systemd_row["source_long"] = "Syslog"
        base_systemd_row["message"] = "COMMAND=/usr/sbin/poweroff"
        assert system_shutdown(base_systemd_row) is None

    def test_returns_none_when_source_long_missing(self, base_systemd_row):
        del base_systemd_row["source_long"]
        base_systemd_row["message"] = "COMMAND=/usr/sbin/poweroff"
        assert system_shutdown(base_systemd_row) is None

    def test_source_long_case_insensitive(self, base_systemd_row):
        base_systemd_row["source_long"] = "SYSTEMD JOURNAL"
        base_systemd_row["message"] = "COMMAND=/usr/sbin/poweroff"
        result = system_shutdown(base_systemd_row)
        assert result is not None

    def test_returns_none_when_message_empty(self, base_systemd_row):
        base_systemd_row["message"] = ""
        assert system_shutdown(base_systemd_row) is None

    def test_returns_none_when_message_missing(self, base_systemd_row):
        del base_systemd_row["message"]
        assert system_shutdown(base_systemd_row) is None

    def test_returns_none_for_unrecognised_message(self, base_systemd_row):
        base_systemd_row["message"] = "Some unrelated journal log line"
        assert system_shutdown(base_systemd_row) is None

    def test_dispatches_to_scheduled_shutdown(self, base_systemd_row):
        base_systemd_row["message"] = (
            "COMMAND=/usr/sbin/shutdown -h 23:30"
        )
        result = system_shutdown(base_systemd_row)
        assert result is not None
        _, activity, _ = result
        assert "scheduled_shutdown" in activity

    def test_dispatches_to_manual_poweroff(self, base_systemd_row):
        base_systemd_row["message"] = "COMMAND=/usr/sbin/poweroff"
        result = system_shutdown(base_systemd_row)
        assert result is not None
        assert result[1] == "cmd_sudo_poweroff"

    def test_dispatches_to_manual_shutdown_now(self, base_systemd_row):
        base_systemd_row["message"] = "COMMAND=/usr/sbin/shutdown now"
        result = system_shutdown(base_systemd_row)
        assert result is not None
        assert result[1] == "cmd_sudo_shutdown_now"

    def test_dispatches_to_manual_init_0(self, base_systemd_row):
        base_systemd_row["message"] = "COMMAND=/usr/sbin/init 0"
        result = system_shutdown(base_systemd_row)
        assert result is not None
        assert result[1] == "cmd_sudo_init_0"

    def test_dispatches_to_shutdown_completion(self, base_systemd_row):
        base_systemd_row["message"] = "Journal stopped"
        result = system_shutdown(base_systemd_row)
        assert result is not None
        assert result[1] == "shutdown_completed"

    def test_dispatches_to_forceful_shutdown(self, base_systemd_row):
        base_systemd_row["message"] = (
            "system.journal corrupted or uncleanly shut down"
        )
        result = system_shutdown(base_systemd_row)
        assert result is not None
        assert result[1] == "forceful_shutdown_detected"


class TestExtractScheduledShutdown:
    """Tests for _extract_scheduled_shutdown()."""

    def test_basic_scheduled_shutdown(self):
        message = "COMMAND=/usr/sbin/shutdown -h 23:30"
        result = _extract_scheduled_shutdown(message, "2024-06-01T10:00:00Z")
        assert result is not None
        label, activity, extra = result
        assert label == "System Running"
        assert "scheduled_shutdown" in activity
        assert "23:30" in activity
        assert extra == "System Running"

    def test_scheduled_time_includes_date_from_datetime_str(self):
        message = "COMMAND=/usr/sbin/shutdown -h 08:00"
        result = _extract_scheduled_shutdown(message, "2024-06-15T07:00:00Z")
        assert result is not None
        assert "2024-06-15" in result[1]
        assert "08:00" in result[1]

    def test_datetime_str_empty_uses_time_only(self):
        message = "COMMAND=/usr/sbin/shutdown -h 22:00"
        result = _extract_scheduled_shutdown(message, "")
        assert result is not None
        assert "22:00" in result[1]

    def test_invalid_datetime_str_falls_back_to_time_only(self):
        message = "COMMAND=/usr/sbin/shutdown -h 14:00"
        result = _extract_scheduled_shutdown(message, "not-a-date")
        assert result is not None
        assert "14:00" in result[1]

    def test_single_digit_hour(self):
        message = "COMMAND=/usr/sbin/shutdown -h 9:00"
        result = _extract_scheduled_shutdown(message, "")
        assert result is not None
        assert "9:00" in result[1]

    def test_no_shutdown_pattern_returns_none(self):
        message = "COMMAND=/usr/sbin/poweroff"
        assert _extract_scheduled_shutdown(message, "") is None

    def test_empty_message_returns_none(self):
        assert _extract_scheduled_shutdown("", "") is None

    def test_shutdown_without_h_flag_returns_none(self):
        """shutdown without -h flag should not match."""
        message = "COMMAND=/usr/sbin/shutdown now"
        assert _extract_scheduled_shutdown(message, "") is None

    def test_activity_starts_with_scheduled_shutdown(self):
        message = "COMMAND=/usr/sbin/shutdown -h 18:30"
        result = _extract_scheduled_shutdown(message, "")
        assert result[1].startswith("scheduled_shutdown_")


class TestExtractManualShutdown:
    """Tests for _extract_manual_shutdown()."""

    def test_poweroff_command(self):
        result = _extract_manual_shutdown("COMMAND=/usr/sbin/poweroff")
        assert result is not None
        label, activity, extra = result
        assert label == "Initiating Shutdown"
        assert activity == "cmd_sudo_poweroff"
        assert extra == "System Running"

    def test_poweroff_with_surrounding_text(self):
        message = "USER=root ; COMMAND=/usr/sbin/poweroff ; ENV=..."
        result = _extract_manual_shutdown(message)
        assert result is not None
        assert result[1] == "cmd_sudo_poweroff"

    def test_poweroff_hyphenated_suffix_matches_due_to_word_boundary(self):
        message = "COMMAND=/usr/sbin/poweroff-extended"
        result = _extract_manual_shutdown(message)
        assert result is not None
        assert result[1] == "cmd_sudo_poweroff"

    def test_shutdown_now_command(self):
        result = _extract_manual_shutdown("COMMAND=/usr/sbin/shutdown now")
        assert result is not None
        assert result[1] == "cmd_sudo_shutdown_now"

    def test_shutdown_now_label_and_extra(self):
        result = _extract_manual_shutdown("COMMAND=/usr/sbin/shutdown now")
        assert result[0] == "Initiating Shutdown"
        assert result[2] == "System Running"

    def test_shutdown_now_with_leading_context(self):
        message = "sudo: user : COMMAND=/usr/sbin/shutdown now"
        result = _extract_manual_shutdown(message)
        assert result is not None
        assert result[1] == "cmd_sudo_shutdown_now"

    def test_init_0_command(self):
        result = _extract_manual_shutdown("COMMAND=/usr/sbin/init 0")
        assert result is not None
        assert result[1] == "cmd_sudo_init_0"

    def test_init_0_label_and_extra(self):
        result = _extract_manual_shutdown("COMMAND=/usr/sbin/init 0")
        assert result[0] == "Initiating Shutdown"
        assert result[2] == "System Running"

    def test_init_1_does_not_match(self):
        message = "COMMAND=/usr/sbin/init 1"
        assert _extract_manual_shutdown(message) is None

    def test_empty_message_returns_none(self):
        assert _extract_manual_shutdown("") is None

    def test_unrelated_command_returns_none(self):
        assert _extract_manual_shutdown("COMMAND=/usr/bin/apt update") is None


class TestExtractShutdownCompletion:
    """Tests for _extract_shutdown_completion()."""

    def test_journal_stopped(self):
        result = _extract_shutdown_completion("Journal stopped")
        assert result is not None
        label, activity, extra = result
        assert label == "System Shutdown"
        assert activity == "shutdown_completed"
        assert extra == "Initiating Shutdown"

    def test_journal_stopped_case_insensitive(self):
        assert _extract_shutdown_completion("JOURNAL STOPPED") is not None
        assert _extract_shutdown_completion("journal stopped") is not None

    def test_journal_stopped_in_full_log_line(self):
        message = "Jun 01 23:45:00 host systemd-journald[123]: Journal stopped"
        result = _extract_shutdown_completion(message)
        assert result is not None
        assert result[1] == "shutdown_completed"

    def test_empty_message_returns_none(self):
        assert _extract_shutdown_completion("") is None

    def test_journal_started_does_not_match(self):
        assert _extract_shutdown_completion("Journal started") is None

    def test_unrelated_message_returns_none(self):
        assert _extract_shutdown_completion("System rebooting normally") is None


class TestExtractForcefulShutdown:
    """Tests for _extract_forceful_shutdown()."""

    def test_unclean_shutdown_message(self):
        message = "system.journal corrupted or uncleanly shut down"
        result = _extract_forceful_shutdown(message)
        assert result is not None
        label, activity, extra = result
        assert label == "System Recovery"
        assert activity == "forceful_shutdown_detected"
        assert extra == "System Running"

    def test_case_insensitive_matching(self):
        message = "SYSTEM.JOURNAL CORRUPTED OR UNCLEANLY SHUT DOWN"
        result = _extract_forceful_shutdown(message)
        assert result is not None
        assert result[1] == "forceful_shutdown_detected"

    def test_message_with_extra_context(self):
        message = (
            "Failed to open system.journal corrupted or uncleanly shut down, "
            "ignoring."
        )
        result = _extract_forceful_shutdown(message)
        assert result is not None
        assert result[1] == "forceful_shutdown_detected"

    def test_empty_message_returns_none(self):
        assert _extract_forceful_shutdown("") is None

    def test_partial_pattern_returns_none(self):
        message = "system.journal corrupted"
        assert _extract_forceful_shutdown(message) is None

    def test_unrelated_message_returns_none(self):
        message = "Journal restarted after clean shutdown"
        assert _extract_forceful_shutdown(message) is None

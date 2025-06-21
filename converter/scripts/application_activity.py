"""
Application Activity Extractor

An application activity extractor that works with systemd journal entries.
This script extracts meaningful information about application activities including:
- Application launches (Started)
- Application terminations (Consumed CPU time)

"""

import re


def application_activity(artifact):
    if artifact.get('source') != 'LOG':
        return None

    source_long = artifact.get('source_long', '')
    if 'systemd journal' not in source_long.lower():
        return None

    message = artifact.get('message', '')
    if not message:
        return None

    start_result = _extract_application_start(message)
    if start_result:
        return start_result

    termination_result = _extract_application_termination(message)
    if termination_result:
        return termination_result

    return None


def _extract_application_start(message):
    """
    Pattern: "Started <scope-name>.scope"
    """
    # Look for Started pattern
    start_pattern = r'Started\s+([^\s]+\.scope)'
    match = re.search(start_pattern, message)

    if match:
        scope_name = match.group(1)
        app_name = _util_app_name_from_scope(scope_name)

        if app_name:
            return app_name, f"launch_{app_name}", None

    return None


def _extract_application_termination(message):
    """
    Pattern: "<scope-name>.scope: Consumed X CPU time"
    """

    consumed_pattern = r'([^\s]+\.scope):\s+Consumed\s+.*\s+CPU\s+time'
    match = re.search(consumed_pattern, message)

    if match:
        scope_name = match.group(1)
        app_name = _util_app_name_from_scope(scope_name)

        if app_name:
            return 'Desktop', f"close_{app_name}", app_name

    return None


def _util_app_name_from_scope(scope_name):
    """
    Extract a clean application name from systemd scope name.
    """

    snap_pattern = r'snap\.([^.]+)\.'
    snap_match = re.search(snap_pattern, scope_name)
    if snap_match:
        app_name = snap_match.group(1)
        return app_name

    gnome_pattern = r'app-gnome-org\.gnome\.([^-]+)'
    gnome_match = re.search(gnome_pattern, scope_name)
    if gnome_match:
        app_name = gnome_match.group(1).lower()
        return app_name

    # app_pattern = r'app-([^-]+)'
    # app_match = re.search(app_pattern, scope_name)
    # if app_match:
    #     app_name = app_match.group(1).lower()
    #     return app_name

    return None

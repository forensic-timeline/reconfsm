"""
System Shutdown Activity Extractor

A system shutdown activity extractor that works with systemd journal entries.
This script extracts meaningful information about system shutdown activities including:
- Scheduled shutdowns
- Manual shutdown commands (poweroff, shutdown now, init 0)
- Shutdown completion events
- Forceful/unclean shutdown detection

"""

import re
from datetime import datetime


def system_shutdown(artifact):
    if artifact.get('source') != 'LOG':
        return None
    source_long = artifact.get('source_long', '')
    if 'systemd journal' not in source_long.lower():
        return None

    message = artifact.get('message', '')
    datetime_str = artifact.get('datetime', '')

    if not message:
        return None

    scheduled_result = _extract_scheduled_shutdown(message, datetime_str)
    if scheduled_result:
        return scheduled_result

    manual_shutdown_result = _extract_manual_shutdown(message)
    if manual_shutdown_result:
        return manual_shutdown_result

    shutdown_complete_result = _extract_shutdown_completion(message)
    if shutdown_complete_result:
        return shutdown_complete_result

    forceful_shutdown_result = _extract_forceful_shutdown(message)
    if forceful_shutdown_result:
        return forceful_shutdown_result

    return None


def _extract_scheduled_shutdown(message, datetime_str):
    """
    Pattern: "COMMAND=/usr/sbin/shutdown -h HH:MM"
    """
    scheduled_pattern = r'COMMAND=/usr/sbin/shutdown\s+-h\s+(\d{1,2}:\d{2})'
    match = re.search(scheduled_pattern, message)

    if match:
        scheduled_time = match.group(1)
        try:
            if datetime_str:
                log_datetime = datetime.fromisoformat(
                    datetime_str.replace('Z', '+00:00'))
                date_part = log_datetime.strftime('%Y-%m-%d')
                full_scheduled_time = f"{date_part} {scheduled_time}"
            else:
                full_scheduled_time = scheduled_time
        except:
            full_scheduled_time = scheduled_time

        return "System Running", f"scheduled_shutdown_{full_scheduled_time}", "System Running"

    return None


def _extract_manual_shutdown(message):
    """
    Patterns:
    - "COMMAND=/usr/sbin/poweroff"
    - "COMMAND=/usr/sbin/shutdown now" 
    - "COMMAND=/usr/sbin/init 0"
    """

    if re.search(r'COMMAND=/usr/sbin/poweroff\b', message):
        return "Initiating Shutdown", "cmd_sudo_poweroff", "System Running"

    if re.search(r'COMMAND=/usr/sbin/shutdown\s+now\b', message):
        return "Initiating Shutdown", "cmd_sudo_shutdown_now", "System Running"

    if re.search(r'COMMAND=/usr/sbin/init\s+0\b', message):
        return "Initiating Shutdown", "cmd_sudo_init_0", "System Running"

    return None


def _extract_shutdown_completion(message):
    """
    Pattern: "Journal stopped"
    """
    if re.search(r'Journal stopped', message, re.IGNORECASE):
        return "System Shutdown", "shutdown_completed", "Initiating Shutdown"
    return None


def _extract_forceful_shutdown(message):
    """
    Pattern: "system.journal corrupted or uncleanly shut down"
    """
    if re.search(r'system\.journal.*corrupted.*or.*uncleanly.*shut.*down', message, re.IGNORECASE):
        return "System Recovery", "forceful_shutdown_detected", "System Running"

    return None

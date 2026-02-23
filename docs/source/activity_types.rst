Supported Activity Types
========================

ReconFSM uses specialized extraction scripts to define the logic for states and transitions. This page details the built-in activity types.

Web Activity (``web_activity``)
-------------------------------

This module reconstructs user browsing behavior, primarily focusing on Firefox history.

*   **Log Sources**: Firefox History (Places database), Page Visited, File Downloaded.
*   **States**:
    *   Specific URLs (e.g., ``Web : google.com``).
    *   Search engine queries.
    *   File download events.
*   **Triggers**:
    *   ``accessed_website_direct``: User typed URL or used a bookmark.
    *   ``accessed_website_link``: User clicked a link.
    *   ``accessed_website_redirect``: Automatic redirection.
    *   ``performed_search``: Submission of search terms.
    *   ``downloaded_file``: Successful file download.

Application Activity (``application_activity``)
-----------------------------------------------

This module tracks the lifecycle of applications running on the system.

*   **Log Sources**: ``systemd`` journal entries, D-Bus messages.
*   **States**:
    *   ``Desktop``: The default state when no tracked app is active.
    *   Specific application names (e.g., ``gnome-terminal``, ``firefox``).
*   **Triggers**:
    *   ``launch_<app_name>``: Application process started.
    *   ``close_<app_name>``: Application process terminated.

System Shutdown (``system_shutdown``)
-------------------------------------

Reconstructs the events leading to and during system power-off sequences.

*   **Log Sources**: ``systemd-logind``, kernel messages.
*   **States**:
    *   ``System Running``: Normal operating state.
    *   ``Initiating Shutdown``: The shutdown signal has been received.
    *   ``System Shutdown``: The system is powering off.
    *   ``System Recovery``: Detected if the system was rebooted after an improper shutdown.
*   **Triggers**:
    *   ``cmd_sudo_poweroff``: User initiated poweroff via sudo.
    *   ``cmd_sudo_shutdown_now``: User initiated shutdown via sudo.
    *   ``shutdown_completed``: Normal sequence finished.
    *   ``forceful_shutdown_detected``: Detected a sudden loss of logs without a clean shutdown signal.

Adding New Activity Types
-------------------------

You can extend ReconFSM by adding your own extraction scripts to ``reconfsm/converter/scripts/``.

A script must:
1.  Be named ``your_type.py``.
2.  Contain a function named ``your_type(row)`` that takes a CSV row (dict) as input.
3.  Return a tuple ``(state, trigger, previous_state)`` or ``None`` if the row is not relevant.

Example Template:

.. code-block:: python

   def my_custom_activity(row):
       if "Keyword" in row['message']:
           return ("TargetState", "trigger_name", None)
       return None

"""
Shared gated-download policy for the Streamlit app and holdout verification.

This is the same decision path that feeds st.download_button(data=...) in app.py.
If this function returns None, the presenter gets no file.
"""
from __future__ import annotations

import os
from typing import Optional

TIMING_TOLERANCE_SECONDS = 3.0


def is_download_unlocked(status: str, measured_seconds: float, target_seconds: float) -> bool:
    """Return True only when the app would show the download button."""
    try:
        gap = float(measured_seconds) - float(target_seconds)
    except (TypeError, ValueError):
        return False
    return status == "PASS" and abs(gap) <= TIMING_TOLERANCE_SECONDS


def get_download_bytes(
    status: str,
    measured_seconds: float,
    target_seconds: float,
    audio_path: Optional[str],
) -> Optional[bytes]:
    """
    Return the exact MP3 bytes the download button would hand over, or None if locked.

    app.py calls this and passes the result to st.download_button(data=...).
    Holdout export writes these same bytes so verification measures presenter downloads.
    """
    if not is_download_unlocked(status, measured_seconds, target_seconds):
        return None
    if not audio_path or not os.path.exists(audio_path):
        return None
    with open(audio_path, "rb") as af:
        return af.read()


def write_download_file(
    status: str,
    measured_seconds: float,
    target_seconds: float,
    source_audio_path: Optional[str],
    dest_path: str,
) -> Optional[str]:
    """
    Persist what the download button would ship.

    Returns dest_path when unlocked and written; otherwise removes any stale dest
    and returns None (download locked / no file for the presenter).
    """
    payload = get_download_bytes(status, measured_seconds, target_seconds, source_audio_path)
    if payload is None:
        if dest_path and os.path.exists(dest_path):
            os.remove(dest_path)
        return None

    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    with open(dest_path, "wb") as df:
        df.write(payload)
    return dest_path

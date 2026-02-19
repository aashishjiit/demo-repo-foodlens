"""Streamlit compatibility helpers.

Provide a stable `rerun()` function that works across Streamlit versions.
Call `st_compat.rerun()` instead of `st.experimental_rerun()`.
"""
from __future__ import annotations

import streamlit as st


def rerun() -> None:
    """Request a rerun of the Streamlit script in a version-agnostic way.

    Tries the documented `st.experimental_rerun()` first. If not present, it
    falls back to raising the internal `RerunException`. As a last resort it
    calls `st.stop()` so execution ends cleanly.
    """
    # Preferred public API when available
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
            return
        except Exception:
            # Continue to other strategies if the call fails for any reason
            pass

    # Try internal Streamlit mechanism
    try:
        from streamlit.runtime.scriptrunner import RerunException

        raise RerunException
    except Exception:
        # Final fallback: stop the script
        try:
            st.stop()
        except Exception:
            # If even that fails, there's nothing sensible to do here.
            return

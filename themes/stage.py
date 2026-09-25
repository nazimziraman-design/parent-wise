"""Thin wrapper: Parent Wise format theme (see themes/pw.py)."""
from themes.pw import *  # noqa: F401,F403
from themes import pw as _pw


def render(data):
    return _pw.render(data)

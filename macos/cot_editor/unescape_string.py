#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Unescape string from double quotes.

Reverse the escaping done by escape_string, converting escaped
sequences back to their original characters. Strips surrounding
double quotes if present.
"""

# %%%{CotEditorXInput=Selection}%%%
# %%%{CotEditorXOutput=ReplaceSelection}%%%

import re
import sys

_UNESCAPE_MAP = {
    r'\n': '\n',
    r'\t': '\t',
    r'\"': '"',
    r'\\': '\\',
}

_UNESCAPE_RE = re.compile(r'\\[nt"\\]')


def _unescape_match(m):
    return _UNESCAPE_MAP[m.group(0)]


def unescape_string(text):
    """Unescape string from double-quoted usage.

    Strips surrounding double quotes if present, then reverses
    the escaping done by escape_string.
    """
    # 去除外层双引号（如果有的话）
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    return _UNESCAPE_RE.sub(_unescape_match, text)


def main():
    in_text = sys.stdin.read()
    if in_text:
        unescaped = unescape_string(in_text)
        sys.stdout.write(unescaped)


if __name__ == "__main__":
    main()
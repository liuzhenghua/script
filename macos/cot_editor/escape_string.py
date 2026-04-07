#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Escape string for double quotes.

Convert special characters so the text can be safely placed inside "".
"""

# %%%{CotEditorXInput=Selection}%%%
# %%%{CotEditorXOutput=ReplaceSelection}%%%

import sys


def escape_string(text):
    """Escape string for double-quoted usage."""
    return (text
            .replace("\\", "\\\\")   # 反斜杠
            .replace('"', '\\"')     # 双引号
            .replace("\n", "\\n")    # 换行
            .replace("\t", "\\t"))   # Tab


def main():
    in_text = sys.stdin.read()
    if in_text:
        escaped = escape_string(in_text)
        # 如果你想自动加双引号就用这一行👇
        # escaped = f'"{escaped}"'
        sys.stdout.write(escaped)


if __name__ == "__main__":
    main()
#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Decode Base64 text.

Decode selected Base64 text and replace it with the decoded content.
Whitespace is ignored, and missing padding is added automatically.
URL-encoded Base64 such as %3D padding is decoded first.
"""

# %%%{CotEditorXInput=Selection}%%%
# %%%{CotEditorXOutput=ReplaceSelection}%%%

import base64
import binascii
import re
import sys
import urllib.parse


def _normalize_base64(text):
    """URL-decode, remove whitespace, and add missing Base64 padding."""
    normalized = urllib.parse.unquote(text)
    normalized = re.sub(r"\s+", "", normalized)
    if not normalized:
        return normalized
    padding = (-len(normalized)) % 4
    return normalized + ("=" * padding)


def base64_decode(text):
    """Decode standard or URL-safe Base64 text into bytes."""
    normalized = _normalize_base64(text)
    try:
        return base64.b64decode(normalized, validate=True)
    except binascii.Error:
        return base64.urlsafe_b64decode(normalized)


def main():
    in_text = sys.stdin.read()
    if not in_text:
        return

    try:
        decoded = base64_decode(in_text)
    except (binascii.Error, ValueError) as exc:
        sys.stderr.write(f"Invalid Base64 input: {exc}\n")
        sys.exit(1)

    sys.stdout.buffer.write(decoded)


if __name__ == "__main__":
    main()

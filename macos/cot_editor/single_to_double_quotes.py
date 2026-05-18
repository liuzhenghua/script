#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Replace single quotes with double quotes in JSON-like text.

Python dict repr uses single quotes for keys/values, which is not valid JSON.
This script replaces ' with " so the text becomes proper JSON.
"""

# %%%{CotEditorXInput=Selection}%%%
# %%%{CotEditorXOutput=ReplaceSelection}%%%

import re
import sys


def single_to_double_quotes(text):
    """Replace single-quoted strings with double-quoted strings.

    Handles escaped single quotes (\\') inside single-quoted strings,
    converting them to unescaped double quotes. Also unescapes \\\'
    sequences properly.
    """
    # 匹配单引号字符串，内部允许转义的单引号 \'
    # 对于 \'，需要变成 "（因为双引号字符串里 ' 不需要转义）
    # 对于 \\'（反斜杠 + 轴义单引号），需要变成 \\"（反斜杠保留，'→"）
    result = []
    i = 0
    while i < len(text):
        if text[i] == "'":
            # 找到单引号字符串的结束位置
            j = i + 1
            while j < len(text):
                if text[j] == "\\" and j + 1 < len(text):
                    if text[j + 1] == "'":
                        j += 2
                        continue
                    j += 2
                    continue
                if text[j] == "'":
                    break
                j += 1
            # 提取字符串内容并转换
            inner = text[i + 1:j]
            # 1. 内容中的双引号需要转义：\" → \"（已经是），" → \"
            inner = inner.replace('\\"', '\x00')  # 先保护已转义的双引号
            inner = inner.replace('"', '\\"')     # 未转义的 " → \"
            inner = inner.replace('\x00', '\\"')  # 恢复已转义的
            # 2. 把 \' → '（双引号字符串中 ' 不需转义）
            #    把 \\' → \\（反斜杠保留，' 不再转义）
            inner = re.sub(r"\\\\'", r"\\\\", inner)
            inner = inner.replace("\\'", "'")
            result.append('"')
            result.append(inner)
            result.append('"')
            i = j + 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def main():
    in_text = sys.stdin.read()
    if in_text:
        converted = single_to_double_quotes(in_text)
        sys.stdout.write(converted)


if __name__ == "__main__":
    main()
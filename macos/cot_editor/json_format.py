#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Format JSON, escaping real newlines/tabs/etc. inside string values first.

When JSON string values contain literal newlines, tabs, or other control
characters, the JSON becomes invalid and tools like jq fail.  This script
first sanitises those characters (converting them to their escaped forms),
then pretty-prints the result.
"""

# %%%{CotEditorXInput=Selection}%%%
# %%%{CotEditorXOutput=ReplaceSelection}%%%

import json
import re
import sys

_CTRL_CHAR_MAP = {
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
    '\b': '\\b',
    '\f': '\\f',
}

# JSON 字符串中合法的转义序列：\" \\ \/ \b \f \n \r \t \uXXXX
_VALID_ESCAPES = set('"\\/bfnrt')

# 字符串结束后的合法后续字符（跳过空白后）
_STRING_END_CHARS = set(':,}]')


def _is_string_end(text, pos):
    """判断 text[pos] 处的双引号是否为字符串的结束引号。

    启发式：跳过引号后的空白，看紧跟的字符是否为 JSON 结构字符
    （冒号、逗号、右花括号、右方括号）。如果是则认为是字符串结束；
    否则认为是值内未转义的引号。
    """
    j = pos + 1
    n = len(text)
    while j < n and text[j] in ' \t\n\r':
        j += 1
    if j >= n:
        return True
    return text[j] in _STRING_END_CHARS


def _fix_string_values(text):
    """将 JSON 文本中字符串值内的控制字符、非法转义、未转义引号修复。

    逐字符扫描，正确处理已有的转义序列（如 \\n），避免重复转义。
    只处理双引号内的字符串值，不影响 JSON 结构本身。
    """
    result = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '"':
            # 进入一个字符串值
            result.append('"')
            i += 1
            while i < n:
                ch = text[i]
                if ch == '\\':
                    # 遇到反斜杠，检查后续转义是否合法
                    i += 1
                    if i < n:
                        next_ch = text[i]
                        if next_ch == 'u' and i + 4 < n:
                            # \uXXXX 形式，原样保留
                            result.append('\\u')
                            result.append(text[i+1:i+5])
                            i += 5
                        elif next_ch in _VALID_ESCAPES:
                            # 合法转义序列，原样保留
                            result.append('\\')
                            result.append(next_ch)
                            i += 1
                        else:
                            # 非法转义序列（如 \c \s \a 等），修复为 \\ + 原字符
                            result.append('\\\\')
                            result.append(next_ch)
                            i += 1
                    else:
                        # 末尾孤立的反斜杠，转义它
                        result.append('\\\\')
                    continue
                if ch == '"':
                    if _is_string_end(text, i):
                        # 字符串结束
                        result.append('"')
                        i += 1
                        break
                    else:
                        # 值内未转义的双引号，转义为 \"
                        result.append('\\"')
                        i += 1
                        continue
                # 检查是否为需要转义的控制字符
                if ch in _CTRL_CHAR_MAP:
                    result.append(_CTRL_CHAR_MAP[ch])
                else:
                    code = ord(ch)
                    if code < 0x20:
                        # 其他控制字符转为 \uXXXX
                        result.append('\\u{:04x}'.format(code))
                    else:
                        result.append(ch)
                i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def main():
    in_text = sys.stdin.read()
    if not in_text:
        return
    # 第一步：修复字符串值中的控制字符
    fixed = _fix_string_values(in_text)
    # 第二步：解析并美化输出
    try:
        obj = json.loads(fixed)
        formatted = json.dumps(obj, ensure_ascii=False, indent=2)
        sys.stdout.write(formatted + '\n')
    except json.JSONDecodeError as e:
        sys.stderr.write('JSON parse error: {}\n'.format(e))
        sys.stdout.write(fixed)


if __name__ == "__main__":
    main()

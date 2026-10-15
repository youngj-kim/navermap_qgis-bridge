# SPDX-License-Identifier: GPL-2.0-or-later
"""Credential validation shared by settings and HTTP boundaries."""


def validated_credential(value):
    value = str(value).strip()
    if not value or any(not 33 <= ord(character) <= 126 for character in value):
        raise ValueError("인증키는 공백 없는 인쇄 가능한 ASCII 문자여야 합니다.")
    return value

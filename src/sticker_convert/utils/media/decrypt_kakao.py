#!/usr/bin/env python3
from __future__ import annotations

from typing import List

# References:
# https://github.com/blluv/KakaoTalkEmoticonDownloader
# https://github.com/star-39/moe-sticker-bot


class DecryptKakao:
    @staticmethod
    def generate_lfsr(key: str) -> List[int]:
        d = list(key * 2)
        seq = [0, 0, 0]

        seq[0] = 301989938
        seq[1] = 623357073
        seq[2] = -2004086252

        i = 0

        for i in range(0, 4):
            seq[0] = ord(d[i]) | (seq[0] << 8)
            seq[1] = ord(d[4 + i]) | (seq[1] << 8)
            seq[2] = ord(d[8 + i]) | (seq[2] << 8)

        seq[0] = seq[0] & 0xFFFFFFFF
        seq[1] = seq[1] & 0xFFFFFFFF
        seq[2] = seq[2] & 0xFFFFFFFF

        return seq

    @staticmethod
    def xor_byte(b: int, seq: List[int]) -> int:
        flag1 = 1
        flag2 = 0
        result = 0
        for _ in range(0, 8):
            v10 = seq[0] >> 1
            if (seq[0] << 31) & 0xFFFFFFFF:
                seq[0] = v10 ^ 0xC0000031
                v12 = seq[1] >> 1
                if (seq[1] << 31) & 0xFFFFFFFF:
                    seq[1] = (v12 | 0xC0000000) ^ 0x20000010
                    flag1 = 1
                else:
                    seq[1] = v12 & 0x3FFFFFFF
                    flag1 = 0
            else:
                seq[0] = v10
                v11 = seq[2] >> 1
                if (seq[2] << 31) & 0xFFFFFFFF:
                    seq[2] = (v11 | 0xF0000000) ^ 0x8000001
                    flag2 = 1
                else:
                    seq[2] = v11 & 0xFFFFFFF
                    flag2 = 0

            result = flag1 ^ flag2 | 2 * result
        return result ^ b

    @staticmethod
    def xor_data(data: bytes) -> bytes:
        dat = list(data)
        s = DecryptKakao.generate_lfsr("a271730728cbe141e47fd9d677e9006d")
        for i in range(0, 128):
            dat[i] = DecryptKakao.xor_byte(dat[i], s)
        return bytes(dat)

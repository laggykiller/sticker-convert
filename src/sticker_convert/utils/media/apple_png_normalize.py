#!/usr/bin/env python3
"""
Required for pack_id < 775 (https://github.com/star-39/moe-sticker-bot/blob/ef2f06f3eb7a833e011e0a5201e007fc130978e7/pkg/msbimport/import_line.go#L68)
Reference: https://stackoverflow.com/a/53622211
"""

import struct
import zlib


class ApplePngNormalize:
    @staticmethod
    def normalize(old_png: bytes) -> bytes:
        png_header = b"\x89PNG\r\n\x1a\n"

        if old_png[:8] != png_header:
            return old_png

        new_png = old_png[:8]

        chunk_pos = len(new_png)
        chunk_d = bytearray()

        found_cgbi = False

        # For each chunk in the PNG file
        width = None
        height = None
        while chunk_pos < len(old_png):
            # Reading chunk
            chunk_length_bytes = old_png[chunk_pos : chunk_pos + 4]
            chunk_length = int(struct.unpack(">L", chunk_length_bytes)[0])
            chunk_type = old_png[chunk_pos + 4 : chunk_pos + 8]
            chunk_data = old_png[chunk_pos + 8 : chunk_pos + 8 + chunk_length]
            chunk_crc = old_png[
                chunk_pos + chunk_length + 8 : chunk_pos + chunk_length + 12
            ]
            chunk_crc = struct.unpack(">L", chunk_crc)[0]
            chunk_pos += chunk_length + 12

            # Parsing the header chunk
            if chunk_type == b"IHDR":
                width = struct.unpack(">L", chunk_data[0:4])[0]
                height = struct.unpack(">L", chunk_data[4:8])[0]

            # Parsing the image chunk
            if chunk_type == b"IDAT":
                # Concatename all image data chunks
                chunk_d += chunk_data
                continue

            # Stopping the PNG file parsing
            if chunk_type == b"IEND":
                if not found_cgbi:
                    return old_png

                assert width
                assert height
                buf_size = width * height * 4 + height
                chunk_data = zlib.decompress(chunk_d, -8, buf_size)

                # Swapping red & blue bytes for each pixel
                chunk_data = bytearray(chunk_data)
                offset = 1
                for _ in range(height):
                    for x in range(width):
                        chunk_data[offset + 4 * x], chunk_data[offset + 4 * x + 2] = (
                            chunk_data[offset + 4 * x + 2],
                            chunk_data[offset + 4 * x],
                        )
                    offset += 1 + 4 * width

                # Compressing the image chunk
                # chunk_data = newdata
                chunk_data = zlib.compress(chunk_data)
                chunk_length = len(chunk_data)
                chunk_crc_idat = zlib.crc32(b"IDAT")
                chunk_crc_data = zlib.crc32(chunk_data, chunk_crc_idat)
                chunk_crc_mod = (chunk_crc_data + 0x100000000) % 0x100000000

                new_png += struct.pack(">L", chunk_length)
                new_png += b"IDAT"
                new_png += chunk_data
                new_png += struct.pack(">L", chunk_crc_mod)

                chunk_crc_type = zlib.crc32(chunk_type)
                new_png += struct.pack(">L", 0)
                new_png += b"IEND"
                new_png += struct.pack(">L", chunk_crc_type)
                break

            # Removing CgBI chunk
            if chunk_type == b"CgBI":
                found_cgbi = True
            else:
                new_png += struct.pack(">L", chunk_length)
                new_png += chunk_type
                if chunk_length > 0:
                    new_png += chunk_data
                new_png += struct.pack(">L", chunk_crc)

        return new_png

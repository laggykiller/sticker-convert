#!/usr/bin/env python3
'''
Required for pack_id < 775 (https://github.com/star-39/moe-sticker-bot/blob/ef2f06f3eb7a833e011e0a5201e007fc130978e7/pkg/msbimport/import_line.go#L68)
Reference: https://stackoverflow.com/a/53622211
'''
import struct
import zlib

class ApplePngNormalize:
    @staticmethod
    def normalize(oldPNG: bytes) -> bytes:
        pngheader = b"\x89PNG\r\n\x1a\n"

        if oldPNG[:8] != pngheader:
            return oldPNG

        newPNG = oldPNG[:8]

        chunkPos = len(newPNG)
        chunkD = bytearray()

        foundCGBi = False

        # For each chunk in the PNG file
        while chunkPos < len(oldPNG):

            # Reading chunk
            chunkLength = oldPNG[chunkPos:chunkPos+4]
            chunkLength = struct.unpack(">L", chunkLength)[0]
            chunkType = oldPNG[chunkPos+4 : chunkPos+8]
            chunkData = oldPNG[chunkPos+8:chunkPos+8+chunkLength] # type: ignore[operator]
            chunkCRC = oldPNG[chunkPos+chunkLength+8:chunkPos+chunkLength+12] # type: ignore[operator]
            chunkCRC = struct.unpack(">L", chunkCRC)[0]
            chunkPos += chunkLength + 12 # type: ignore[operator]

            # Parsing the header chunk
            if chunkType == b"IHDR":
                width = struct.unpack(">L", chunkData[0:4])[0]
                height = struct.unpack(">L", chunkData[4:8])[0]

            # Parsing the image chunk
            if chunkType == b"IDAT":
                # Concatename all image data chunks
                chunkD += chunkData
                continue

            # Stopping the PNG file parsing
            if chunkType == b"IEND":
                if not foundCGBi:
                    return oldPNG

                bufSize = width * height * 4 + height
                chunkData = zlib.decompress(chunkD, -8, bufSize)

                # Swapping red & blue bytes for each pixel
                chunkData = bytearray(chunkData)
                offset = 1
                for y in range(height):
                    for x in range(width):
                        chunkData[offset+4*x],chunkData[offset+4*x+2] = chunkData[offset+4*x+2],chunkData[offset+4*x]
                    offset += 1+4*width

                # Compressing the image chunk
                #chunkData = newdata
                chunkData = zlib.compress( chunkData )
                chunkLength = len( chunkData ) # type: ignore[assignment]
                chunkCRC = zlib.crc32(b'IDAT') # type: ignore[assignment]
                chunkCRC = zlib.crc32(chunkData, chunkCRC) # type: ignore[assignment, arg-type]
                chunkCRC = (chunkCRC + 0x100000000) % 0x100000000 # type: ignore[operator]

                newPNG += struct.pack(">L", chunkLength)
                newPNG += b'IDAT'
                newPNG += chunkData
                newPNG += struct.pack(">L", chunkCRC)

                chunkCRC = zlib.crc32(chunkType) # type: ignore[assignment]
                newPNG += struct.pack(">L", 0)
                newPNG += b'IEND'
                newPNG += struct.pack(">L", chunkCRC)
                break

            # Removing CgBI chunk
            if chunkType == b"CgBI":
                foundCGBi = True
            else:
                newPNG += struct.pack(">L", chunkLength)
                newPNG += chunkType
                if chunkLength > 0: # type: ignore[operator]
                    newPNG += chunkData
                newPNG += struct.pack(">L", chunkCRC)

        return newPNG
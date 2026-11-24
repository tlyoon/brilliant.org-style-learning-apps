"""Independent stdlib PNG parser and pixel readback, no Selenium dependency.

Checks stored Chrome screenshot pixels against independently known production
CSS arrow colors. Rejects tampered/blank/corrupt PNGs, not scientific meaning.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import struct
import zlib


def _paeth(a:int,b:int,c:int)->int:
    p=a+b-c
    distances=(abs(p-a),abs(p-b),abs(p-c))
    return (a,b,c)[distances.index(min(distances))]


def validate_private_raster_png(path:Path)->dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("BSA258_INDEPENDENT_SCREENSHOT_FILE_MISSING")
    raw=path.read_bytes()
    if not (1000<len(raw)<400000 and
            raw[:8]==bytes.fromhex("89504e470d0a1a0a")):
        raise ValueError("BSA258_INDEPENDENT_REAL_PNG_SIGNATURE_INVALID")
    position=8
    body=[]
    width=height=components=None
    while position<len(raw):
        if position+12>len(raw):
            raise ValueError("BSA258_PNG_TRUNCATED")
        n=struct.unpack(">I",raw[position:position+4])[0]
        tag=raw[position+4:position+8]
        data=raw[position+8:position+8+n]
        crc=raw[position+8+n:position+12+n]
        if len(data)!=n or len(crc)!=4 or (
                zlib.crc32(tag+data)&0xffffffff
                !=struct.unpack(">I",crc)[0]):
            raise ValueError("BSA258_PNG_CRC_OR_LENGTH_INVALID")
        position+=12+n
        if tag==b"IHDR":
            if len(data)!=13:
                raise ValueError("BSA258_PNG_BAD_IHDR")
            width,height,depth,mode,compression,filtering,interlace=(
                struct.unpack(">IIBBBBB",data))
            if ((width,height)!=(640,360) or depth!=8
                    or mode not in (2,6) or compression!=0
                    or filtering!=0 or interlace!=0):
                raise ValueError("BSA258_PNG_UNEXPECTED_SCREENSHOT_FORMAT")
            components=3 if mode==2 else 4
        elif tag==b"IDAT":
            body.append(data)
        elif tag==b"IEND":
            break
    if components is None or not body:
        raise ValueError("BSA258_PNG_NO_RGBA_DATA")
    decompressed=zlib.decompress(b"".join(body))
    pitch=width*components
    if len(decompressed)!=(pitch+1)*height:
        raise ValueError("BSA258_PNG_DECOMPRESSED_ROW_LENGTH_INVALID")
    pixels={}
    wanted={(x,y) for y in range(189,194)
            for x in list(range(147,154))+list(range(477,484))}
    wanted.update({(150,145),(480,145)})
    old=bytearray(pitch)
    offset=0
    for y in range(height):
        mode=decompressed[offset]
        offset+=1
        row=bytearray(decompressed[offset:offset+pitch])
        offset+=pitch
        if mode>4:
            raise ValueError("BSA258_PNG_FILTER_UNSUPPORTED")
        for i in range(pitch):
            a=row[i-components] if i>=components else 0
            b=old[i]
            c=old[i-components] if i>=components else 0
            if mode==1:
                row[i]=(row[i]+a)&255
            elif mode==2:
                row[i]=(row[i]+b)&255
            elif mode==3:
                row[i]=(row[i]+((a+b)//2))&255
            elif mode==4:
                row[i]=(row[i]+_paeth(a,b,c))&255
        for x in set(x for x,py in wanted if py==y):
            px=tuple(row[x*components:(x+1)*components])
            pixels[(x,y)]=px if components==4 else px+(255,)
        old=row
    def near(px,rgb):
        return px[3]>=245 and all(abs(px[i]-rgb[i])<=36 for i in range(3))
    left=sum(near(pixels[(x,y)],(23,107,81))
             for x in range(147,154) for y in range(189,194))
    right=sum(near(pixels[(x,y)],(217,119,6))
              for x in range(477,484) for y in range(189,194))
    if (left<9 or right<9
            or near(pixels[(150,145)],(23,107,81))
            or near(pixels[(480,145)],(217,119,6))):
        raise ValueError("BSA258_INDEPENDENT_PNG_ARROW_PIXELS_DO_NOT_MATCH")
    return {
        "pngSha256":sha256(raw).hexdigest(),
        "width":width,"height":height,
        "independentLeftwardArrowPixels":left,
        "independentRightwardArrowPixels":right,
        "verifiedOppositeVelocityArrows":2,
    }

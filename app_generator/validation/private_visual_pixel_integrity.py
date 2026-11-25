"""Check real private browser screenshot pixels, never diagram semantics.

Only source/package/hash-bound Chrome PNG captures are accepted. This catches
empty, near-uniform or un-decodable renders as technical visual defects; it
cannot certify layout, translations, scientific drawings, accessibility, or
academic PASS. No pixels, textbook material, or screenshots enter reports.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import struct
from typing import Any
import zlib

from app_generator.validation.private_browser_visual_evidence import (
    verify_browser_visual_evidence,
)

_SIGNATURE=b"\x89PNG\r\n\x1a\n"
# Chrome browser screenshots currently use noninterlaced RGB 8-bit PNG.
_MAX_IMAGE_BYTES=8_000_000
_MIN_NONWHITE_RATIO=0.002
_MIN_DISTINCT_SAMPLED_COLORS=4


def _png_rgb_pixels(data: bytes) -> tuple[int,int,bytes]:
    """Decode bounded noninterlaced RGB PNG scanlines, including PNG filters."""
    if data[:8]!=_SIGNATURE:
        raise ValueError("image is not PNG")
    pos=8
    dimensions=None
    parts=[]
    ended=False
    while pos<len(data):
        if pos+12>len(data):
            raise ValueError("truncated PNG chunk")
        count=struct.unpack(">I",data[pos:pos+4])[0]
        label=data[pos+4:pos+8]
        end=pos+12+count
        if count>_MAX_IMAGE_BYTES or end>len(data):
            raise ValueError("oversize/truncated PNG chunk")
        payload=data[pos+8:pos+8+count]
        check=struct.unpack(">I",data[pos+8+count:end])[0]
        if zlib.crc32(label+payload)&0xffffffff != check:
            raise ValueError("PNG chunk CRC mismatch")
        if label==b"IHDR":
            if dimensions is not None or count!=13:
                raise ValueError("duplicate/invalid PNG header")
            w,h,depth,ctype,compression,flt,interlace=struct.unpack(">IIBBBBB",payload)
            if (not 100<=w<=1800 or not 80<=h<=1000 or
                    (depth,ctype,compression,flt,interlace)!=(8,2,0,0,0)):
                raise ValueError("unsupported PNG screenshot format")
            dimensions=(w,h)
        elif label==b"IDAT":
            if dimensions is None:
                raise ValueError("PNG image missing header")
            parts.append(payload)
        elif label==b"IEND":
            if count!=0:
                raise ValueError("bad PNG terminator")
            ended=True
            if end!=len(data):
                raise ValueError("trailing PNG bytes")
            break
        pos=end
    if not ended or not dimensions or not parts:
        raise ValueError("incomplete PNG")
    w,h=dimensions
    stride=w*3
    expected=(stride+1)*h
    if expected>_MAX_IMAGE_BYTES:
        raise ValueError("decoded screenshot too large")
    decoder=zlib.decompressobj()
    raw=decoder.decompress(b"".join(parts),expected+1)
    if (len(raw)!=expected or decoder.unconsumed_tail or
            decoder.unused_data or not decoder.eof):
        raise ValueError("decoded PNG length/compression invalid")
    prev=bytearray(stride)
    pixels=bytearray(stride*h)
    for y in range(h):
        offset=y*(stride+1)
        mode=raw[offset]
        src=raw[offset+1:offset+1+stride]
        dst=bytearray(stride)
        if mode not in (0,1,2,3,4):
            raise ValueError("unsupported PNG filter")
        for x,val in enumerate(src):
            left=dst[x-3] if x>=3 else 0
            up=prev[x]
            above_left=prev[x-3] if x>=3 else 0
            if mode==0:
                pred=0
            elif mode==1:
                pred=left
            elif mode==2:
                pred=up
            elif mode==3:
                pred=(left+up)//2
            else:
                base=left+up-above_left
                distances=(abs(base-left),abs(base-up),abs(base-above_left))
                pred=(left,up,above_left)[distances.index(min(distances))]
            dst[x]=(val+pred)&255
        pixels[y*stride:(y+1)*stride]=dst
        prev=dst
    return w,h,bytes(pixels)


def audit_private_visual_pixel_integrity(
    *, package_file: Path, source_pdf: Path, evidence_dir: Path,
    expected_package_sha256: str, expected_source_sha256: str,
) -> dict[str, Any]:
    """Verify screenshot hashes first, then independently inspect RGB content."""
    identity=verify_browser_visual_evidence(
        package_file=package_file,source_pdf=source_pdf,
        evidence_dir=evidence_dir,
        expected_package_sha256=expected_package_sha256,
        expected_source_sha256=expected_source_sha256)
    manifest=json.loads((evidence_dir/"review-manifest.json").read_text(encoding="utf-8"))
    rows=[]
    for row in manifest["screenshots"]:
        path=evidence_dir/row["file"]
        raw=path.read_bytes()
        if sha256(raw).hexdigest()!=row["sha256"]:
            raise ValueError("screenshot changed after browser verification")
        w,h,pixels=_png_rgb_pixels(raw)
        # An all-white or near-empty screenshot is not a meaningful capture.
        count=w*h
        nonwhite=0
        sample=set()
        for i in range(0,len(pixels),3):
            rgb=(pixels[i],pixels[i+1],pixels[i+2])
            if min(rgb)<245:
                nonwhite+=1
            if (i//3)%16==0:
                sample.add(rgb)
        ratio=nonwhite/count
        if ratio<_MIN_NONWHITE_RATIO or len(sample)<_MIN_DISTINCT_SAMPLED_COLORS:
            raise ValueError("blank or near-uniform browser screenshot")
        rows.append({"activityId":row["activityId"],"locale":row["locale"],
                     "viewportWidth":row["viewportWidth"],
                     "width":w,"height":h,
                     "nonwhitePixelPercent":round(100*ratio,3),
                     "distinctSampleColors":len(sample)})
    return {
        "status":"SOURCE_BOUND_SCREENSHOT_PIXELS_NONBLANK",
        "packageSha256":expected_package_sha256,
        "sourceSha256":expected_source_sha256,
        "screenCapturesChecked":len(rows),
        "technicalPixelIntegrityChecked":True,
        "pixelQualityReviewed":False,
        "academicAccuracyReviewed":False,
        "academicQA":"REVIEW_REQUIRED",
        "publicationAuthorized":False,
        "checks":rows,
        "sourceIdentityStatus":identity["status"],
    }

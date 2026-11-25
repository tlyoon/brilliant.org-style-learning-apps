"""Reproducible private original Figure 9.9 source/raster identity receipt.

Only text labels and successful deterministic rasterization are machine
verified. Physical meaning of pixels is not automatically certified.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from typing import Any
from app_generator.validation.source_passages import extract_pages


def audit_cradle_original_figure(source_pdf:Path)->dict[str,Any]:
    pages=extract_pages(source_pdf)
    if len(pages)<5:
        raise ValueError("physical textbook Figure 9.9 page missing")
    text=pages[4].casefold()
    required=("figure 9.9","example 9.4","this can happen",
              "this cannot happen","kinetic energy")
    if not all(text.count(term)>=1 for term in required):
        raise ValueError("source figure and explanatory labels unlocated")
    # Windows Poppler may create "-.jpg" instead of streaming JPEG on stdout.
    # Render only under an ephemeral PRIVATE folder, never inside Git or Drive.
    with TemporaryDirectory(prefix="cradle-figure-",dir=source_pdf.parent) as folder:
        prefix=Path(folder)/"original-figure-9-9"
        proc=subprocess.run([
            "pdftoppm","-f","5","-l","5","-scale-to","900",
            "-singlefile","-jpeg","-jpegopt","quality=60",
            str(source_pdf),str(prefix),
        ],capture_output=True,timeout=45,check=False)
        raster=prefix.with_suffix(".jpg")
        if proc.returncode!=0 or not raster.is_file():
            raise ValueError("private original-source page image rendering failed")
        data=raster.read_bytes()
        if (len(data)<10000 or not data.startswith(b"\xff\xd8") or
                not data.endswith(b"\xff\xd9")):
            raise ValueError("original raster invalid or truncated")
    return {
       "figure":"9.9",
       "physicalPdfPage":5,
       "originalPdfSha256":sha256(source_pdf.read_bytes()).hexdigest(),
       "originalPageRasterSha256":sha256(data).hexdigest(),
       "originalPageRasterBytes":len(data),
       "diagramHasTwoDistinctLabeledOutcomes":True,
       "visualPhysicsMeaningMachineVerified":False,
       "externalSourceOrImageUploaded":False,
    }

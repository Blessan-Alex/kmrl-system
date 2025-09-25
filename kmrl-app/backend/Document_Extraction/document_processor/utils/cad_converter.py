"""
Utilities to convert CAD formats (e.g., DWG -> DXF) using external tools.

Supported converters (first available is used):
- dwg2dxf (LibreDWG - package: libredwg-tools)
- ODAFileConverter / TeighaFileConverter (Open Design Alliance)
- qcad (CLI export)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def find_dwg_converter() -> Tuple[str, str]:
    """
    Find an installed DWG->DXF converter.

    Returns:
        (tool_name, executable_path)

    Raises:
        FileNotFoundError if no converter found
    """
    candidates = [
        ("dwg2dxf", _which("dwg2dxf")),  # LibreDWG
        ("ODAFileConverter", _which("ODAFileConverter")),  # ODA/Teigha (Linux package name varies)
        ("TeighaFileConverter", _which("TeighaFileConverter")),
        ("qcad", _which("qcad")),
    ]
    for name, path in candidates:
        if path:
            return name, path
    raise FileNotFoundError(
        "No DWG converter found. Install one of: libredwg-tools (dwg2dxf), ODA File Converter, or QCAD."
    )


def convert_dwg_to_dxf(input_path: str, output_dir: Optional[str] = None) -> Path:
    """
    Convert a DWG file to DXF using the first available converter.

    Args:
        input_path: Path to DWG file
        output_dir: Optional output directory; temp dir if None

    Returns:
        Path to the generated DXF file

    Raises:
        RuntimeError on conversion failure
    """
    in_path = Path(input_path).resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"DWG not found: {in_path}")

    tool, exe = find_dwg_converter()
    logger.info(f"Using DWG converter: {tool} ({exe})")

    out_dir = Path(output_dir).resolve() if output_dir else Path(tempfile.mkdtemp(prefix="dwg2dxf_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    dxf_path = out_dir / (in_path.stem + ".dxf")

    try:
        if tool == "dwg2dxf":
            # LibreDWG dwg2dxf: dwg2dxf input.dwg output.dxf
            cmd = [exe, str(in_path), str(dxf_path)]
        elif tool in ("ODAFileConverter", "TeighaFileConverter"):
            # ODA/Teigha CLI usage varies; common pattern:
            # ODAFileConverter <in_dir> <out_dir> <inputVer> <outputVer> <recursive> <audit> <outType>
            # We'll use input dir = file's parent, output dir = out_dir, outType = 1 (DXF)
            cmd = [
                exe,
                str(in_path.parent),
                str(out_dir),
                "ACAD2018",  # input version autodetect usually ok
                "ACAD2018",  # output version
                "0",         # recursive
                "0",         # audit
                "1",         # outType: 1 = DXF
            ]
        elif tool == "qcad":
            # QCAD CLI export: qcad -no-show -autostart script.js ... is complex.
            # Many builds provide qcadcorecmd (headless). Try simple export if available.
            qcad_core = _which("qcadcorecmd")
            if qcad_core:
                cmd = [qcad_core, "-if", str(in_path), "-of", str(dxf_path)]
            else:
                raise RuntimeError("qcad (GUI) detected but headless export not available. Install qcadcorecmd.")
        else:
            raise RuntimeError(f"Unsupported converter tool: {tool}")

        logger.info(f"Converting DWG -> DXF: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Conversion failed with {tool}: {result.stderr or result.stdout}")

        # ODA converter outputs into out_dir with same basename
        if not dxf_path.exists():
            # attempt to locate produced DXF
            produced = list(out_dir.glob(in_path.stem + "*.dxf"))
            if produced:
                dxf_path = produced[0]

        if not dxf_path.exists():
            raise RuntimeError("DXF output not found after conversion.")

        logger.info(f"DWG converted to DXF: {dxf_path}")
        return dxf_path

    except Exception as e:
        logger.error(f"DWG->DXF conversion error: {e}")
        raise



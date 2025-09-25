"""
CAD parsing utilities:
- DWG: convert to DXF via ODA File Converter (CLI), then parse
- DXF: parse via ezdxf (layers, TEXT/MTEXT, entity counts, modelspace bbox)
- IGES: parse via pythonOCC/OCP, compute bbox and topology counts

All functions return JSON-serializable dicts.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from loguru import logger

try:
	import ezdxf
	from ezdxf.entities import DXFEntity
	EZDXF_AVAILABLE = True
except Exception:
	EZDXF_AVAILABLE = False

# Try OCP (pythonocc-core alternative import path)
OCCT_AVAILABLE = False
try:
	# Prefer OCP namespace if available
	from OCP.IGESControl import IGESControl_Reader
	from OCP.Interface import Interface_Static_SetCVal
	from OCP.BRepBndLib import brepbndlib_Add
	from OCP.Bnd import Bnd_Box
	from OCP.TopoDS import TopoDS_Shape
	from OCP.TopExp import TopExp_Explorer
	from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX
	from OCP.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
	from OCP.GProp import GProp_GProps
	OCCT_AVAILABLE = True
except Exception:
	try:
		# Fallback to OCC.Core
		from OCC.Core.IGESControl import IGESControl_Reader
		from OCC.Core.Interface import Interface_Static_SetCVal
		from OCC.Core.BRepBndLib import brepbndlib_Add
		from OCC.Core.Bnd import Bnd_Box
		from OCC.Core.TopoDS import TopoDS_Shape
		from OCC.Core.TopExp import TopExp_Explorer
		from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX
		from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
		from OCC.Core.GProp import GProp_GProps
		OCCT_AVAILABLE = True
	except Exception:
		OCCT_AVAILABLE = False


# ---------------------- DWG Handling ----------------------

def find_oda_converter() -> Optional[str]:
	"""Find ODA File Converter CLI in PATH or common locations."""
	candidates = [
		shutil.which("OdaFileConverter"),
		shutil.which("ODAFileConverter"),
		"/usr/bin/OdaFileConverter",
		"/usr/local/bin/OdaFileConverter",
		"/opt/ODAFileConverter/OdaFileConverter",
	]
	for c in candidates:
		if c and Path(c).exists():
			return c
	return None


def find_libredwg() -> Optional[str]:
	"""Find libredwg CLI tools."""
	for cmd in ["dwg2dxf", "dwgread"]:
		if shutil.which(cmd):
			return cmd
	return None


def convert_dwg_to_dxf_via_libredwg(dwg_path: str, out_dir: str) -> str:
	"""
	Convert DWG to DXF using libredwg (free alternative).
	
	Args:
		dwg_path: Path to input DWG file
		out_dir: Output directory for DXF file
		
	Returns:
		Path to converted DXF file
		
	Raises:
		RuntimeError: If conversion fails
	"""
	libredwg_cmd = find_libredwg()
	if not libredwg_cmd:
		raise RuntimeError("No DWG converter found. Install libredwg-tools: sudo apt install libredwg-tools")
	
	out_dir = Path(out_dir)
	out_dir.mkdir(parents=True, exist_ok=True)
	
	dwg_file = Path(dwg_path)
	dxf_file = out_dir / f"{dwg_file.stem}.dxf"
	
	try:
		# Use dwg2dxf for conversion
		cmd = [libredwg_cmd, "-o", str(dxf_file), dwg_path]
		logger.info(f"Converting DWG to DXF: {' '.join(cmd)}")
		
		result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
		if result.returncode != 0:
			raise RuntimeError(f"libredwg conversion failed: {result.stderr}")
			
		if not dxf_file.exists():
			raise RuntimeError("DXF file was not created")
			
		logger.info(f"Successfully converted DWG to DXF: {dxf_file}")
		return str(dxf_file)
		
	except subprocess.TimeoutExpired:
		raise RuntimeError("DWG conversion timed out")
	except Exception as e:
		raise RuntimeError(f"Failed to convert DWG: {e}")


def convert_dwg_to_dxf_via_oda(dwg_path: str, out_dir: str, version: str = "ACAD2018") -> str:
	"""
	Convert DWG to DXF using ODA File Converter CLI.

	Args:
		dwg_path: Input DWG file path
		out_dir: Output directory for DXF
		version: DXF version (e.g., ACAD2018)

	Returns:
		Path to generated DXF file
	"""
	oda = find_oda_converter()
	if not oda:
		raise RuntimeError(
			"ODA File Converter not found. Install ODAFileConverter and ensure it is on PATH."
		)

	dwg = Path(dwg_path)
	out = Path(out_dir)
	out.mkdir(parents=True, exist_ok=True)
	dxf_path = out / (dwg.stem + ".dxf")

	# ODA CLI usage typically: OdaFileConverter <in_dir> <out_dir> <in_ver> <out_ver> <audit> <recursive>
	# We'll run for a single file by using its directory and filtering later.
	cmd = [
		oda,
		str(dwg.parent),
		str(out),
		"ACAD2018",  # input version autodetect generally ok
		version,
		"1",  # audit
		"0",  # non-recursive
	]
	logger.info(f"Running ODA converter: {' '.join(cmd)}")
	subprocess.run(cmd, check=True)

	if not dxf_path.exists():
		# Some versions preserve subfolders; search
		candidates = list(out.glob(f"**/{dwg.stem}.dxf"))
		if candidates:
			return str(candidates[0].resolve())
		raise RuntimeError("DXF not found after ODA conversion")
	return str(dxf_path.resolve())


# ---------------------- DXF Handling ----------------------

@dataclass
class DXFParseResult:
	layers: List[str]
	texts: List[str]
	entity_counts: Dict[str, int]
	bbox: Tuple[float, float, float, float]


def _update_bbox(bbox: List[float], x: float, y: float) -> None:
	bbox[0] = min(bbox[0], x)
	bbox[1] = min(bbox[1], y)
	bbox[2] = max(bbox[2], x)
	bbox[3] = max(bbox[3], y)


def _entity_bbox_2d(entity: "DXFEntity", bbox: List[float]) -> None:
	"""Best-effort 2D bbox accumulation for common DXF entities."""
	try:
		et = entity.dxftype()
		d = entity.dxf
		if et == "LINE":
			_update_bbox(bbox, float(d.start.x), float(d.start.y))
			_update_bbox(bbox, float(d.end.x), float(d.end.y))
		elif et in ("LWPOLYLINE", "POLYLINE"):
			for v in getattr(entity, "vertices", []):
				_update_bbox(bbox, float(v.dxf.x), float(v.dxf.y))
			for p in getattr(entity, "points", []):
				_update_bbox(bbox, float(p[0]), float(p[1]))
		elif et == "CIRCLE":
			cx, cy, r = float(d.center.x), float(d.center.y), float(d.radius)
			_update_bbox(bbox, cx - r, cy - r)
			_update_bbox(bbox, cx + r, cy + r)
		elif et == "ARC":
			cx, cy, r = float(d.center.x), float(d.center.y), float(d.radius)
			_update_bbox(bbox, cx - r, cy - r)
			_update_bbox(bbox, cx + r, cy + r)
		elif et in ("SPLINE", "ELLIPSE"):
			# Approximate using control points if available
			for p in getattr(entity, "control_points", []):
				_update_bbox(bbox, float(p[0]), float(p[1]))
		elif et in ("TEXT", "MTEXT"):
			ip = getattr(d, "insert", None)
			if ip is not None:
				_update_bbox(bbox, float(ip.x), float(ip.y))
	except Exception:
		return


def parse_dxf(dxf_path: str) -> Dict[str, Any]:
	if not EZDXF_AVAILABLE:
		raise RuntimeError("ezdxf not installed. pip install ezdxf")

	doc = ezdxf.readfile(dxf_path)
	msp = doc.modelspace()

	# Layers
	layers = [layer.dxf.name for layer in doc.layers]

	# Texts and counts
	texts: List[str] = []
	counts: Dict[str, int] = {}
	bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]

	# Technical metadata extraction
	technical_metadata = _extract_technical_metadata(doc)
	
	for e in msp:
		et = e.dxftype()
		counts[et] = counts.get(et, 0) + 1
		if et == "TEXT":
			try:
				texts.append(e.dxf.text)
			except Exception:
				pass
		elif et == "MTEXT":
			try:
				texts.append(e.plain_text())
			except Exception:
				pass
		_entity_bbox_2d(e, bbox)

	# Normalize bbox in case of empty content
	if bbox[0] == float("inf"):
		bbox = [0.0, 0.0, 0.0, 0.0]

	result = {
		"dxf_version": doc.dxfversion,
		"layers": layers,
		"texts": texts,
		"entity_counts": counts,
		"bbox_modelspace": {
			"xmin": bbox[0],
			"ymin": bbox[1],
			"xmax": bbox[2],
			"ymax": bbox[3],
		},
		"technical_metadata": technical_metadata,
	}
	return result


def _extract_technical_metadata(doc) -> Dict[str, Any]:
	"""Extract comprehensive technical metadata from DXF document."""
	metadata = {
		"part_names": [],
		"revision_numbers": [],
		"author": None,
		"creation_date": None,
		"units": None,
		"materials": [],
		"dimensions": [],
		"tolerances": [],
		"weight": None,
		"material_properties": {},
		"drawing_info": {}
	}
	
	try:
		# Header information
		header = doc.header
		metadata["author"] = header.get("$LOGINNAME", "")
		metadata["creation_date"] = header.get("$TDCREATE", "")
		metadata["units"] = _get_units_from_header(header)
		
		# Drawing info from header
		metadata["drawing_info"] = {
			"title": header.get("$TITLE", ""),
			"subject": header.get("$SUBJECT", ""),
			"keywords": header.get("$KEYWORDS", ""),
			"comments": header.get("$COMMENTS", ""),
			"last_saved": header.get("$TDUPDATE", ""),
			"version": header.get("$ACADVER", "")
		}
		
		# Extract from modelspace entities
		msp = doc.modelspace()
		for entity in msp:
			_extract_entity_metadata(entity, metadata)
			
		# Extract from blocks (common for part names)
		for block in doc.blocks:
			try:
				# Check if block is not anonymous (different API versions)
				is_anonymous = getattr(block, 'is_anonymous', lambda: False)()
				if not is_anonymous:
					metadata["part_names"].append(block.name)
					for entity in block:
						_extract_entity_metadata(entity, metadata)
			except Exception:
				# Fallback: just add the block name
				metadata["part_names"].append(block.name)
					
	except Exception as e:
		logger.warning(f"Error extracting technical metadata: {e}")
		
	return metadata


def _get_units_from_header(header) -> str:
	"""Extract units from DXF header."""
	unit_code = header.get("$INSUNITS", 0)
	unit_map = {
		0: "Unitless",
		1: "Inches", 
		2: "Feet",
		3: "Miles",
		4: "Millimeters",
		5: "Centimeters", 
		6: "Meters",
		7: "Kilometers",
		8: "Microinches",
		9: "Mils",
		10: "Yards",
		11: "Angstroms",
		12: "Nanometers",
		13: "Microns",
		14: "Decimeters",
		15: "Decameters",
		16: "Hectometers",
		17: "Gigameters",
		18: "Astronomical units",
		19: "Light years",
		20: "Parsecs"
	}
	return unit_map.get(unit_code, f"Unknown ({unit_code})")


def _extract_entity_metadata(entity, metadata: Dict[str, Any]) -> None:
	"""Extract technical metadata from individual entities."""
	try:
		entity_type = entity.dxftype()
		
		# Extract text content for analysis
		text_content = ""
		if entity_type == "TEXT":
			text_content = entity.dxf.text
		elif entity_type == "MTEXT":
			text_content = entity.plain_text()
		elif entity_type == "ATTRIB":
			text_content = entity.dxf.text
			
		if text_content:
			text_upper = text_content.upper()
			
			# Part names (common patterns)
			if any(keyword in text_upper for keyword in ["PART", "COMPONENT", "ASSEMBLY", "ITEM"]):
				metadata["part_names"].append(text_content.strip())
				
			# Revision numbers
			if any(keyword in text_upper for keyword in ["REV", "REVISION", "VERSION", "VER"]):
				metadata["revision_numbers"].append(text_content.strip())
				
			# Materials
			if any(keyword in text_upper for keyword in ["MATERIAL", "STEEL", "ALUMINUM", "PLASTIC", "WOOD", "CONCRETE"]):
				metadata["materials"].append(text_content.strip())
				
			# Dimensions
			if any(keyword in text_upper for keyword in ["DIM", "DIMENSION", "SIZE", "LENGTH", "WIDTH", "HEIGHT"]):
				metadata["dimensions"].append(text_content.strip())
				
			# Tolerances
			if any(keyword in text_upper for keyword in ["TOL", "TOLERANCE", "±", "+/-"]):
				metadata["tolerances"].append(text_content.strip())
				
			# Weight
			if any(keyword in text_upper for keyword in ["WEIGHT", "MASS", "KG", "LB", "POUND"]):
				metadata["weight"] = text_content.strip()
				
		# Extract dimension entities specifically
		if entity_type == "DIMENSION":
			try:
				dim_text = entity.dxf.text if hasattr(entity.dxf, 'text') else ""
				if dim_text:
					metadata["dimensions"].append(dim_text)
			except Exception:
				pass
				
		# Extract layer information for materials
		layer_name = getattr(entity.dxf, 'layer', '0')
		if layer_name and layer_name != '0':
			# Check if layer name suggests material
			layer_upper = layer_name.upper()
			if any(mat in layer_upper for mat in ["STEEL", "ALUMINUM", "PLASTIC", "WOOD", "CONCRETE", "MATERIAL"]):
				metadata["materials"].append(f"Layer: {layer_name}")
				
	except Exception as e:
		logger.debug(f"Error extracting metadata from entity {entity_type}: {e}")


def _extract_dwg_metadata_only(dwg_path: str) -> Dict[str, Any]:
	"""Extract basic metadata from DWG file when conversion is not available."""
	file_path = Path(dwg_path)
	
	# Basic file metadata
	metadata = {
		"source": file_path.name,
		"from_dwg": True,
		"dxf_path": None,
		"dxf_data": {
			"dxf_version": "Unknown (DWG format)",
			"layers": [],
			"texts": [],
			"entity_counts": {},
			"bbox_modelspace": {
				"xmin": 0.0,
				"ymin": 0.0,
				"xmax": 0.0,
				"ymax": 0.0
			},
			"technical_metadata": {
				"part_names": [],
				"revision_numbers": [],
				"author": "Unknown",
				"creation_date": None,
				"units": "Unknown",
				"materials": [],
				"dimensions": [],
				"tolerances": [],
				"weight": None,
				"material_properties": {},
				"drawing_info": {
					"title": "",
					"subject": "",
					"keywords": "",
					"comments": "",
					"last_saved": "",
					"version": "DWG Format"
				}
			}
		}
	}
	
	# Try to extract basic file information
	try:
		file_size = file_path.stat().st_size
		metadata["dxf_data"]["file_size"] = file_size
		metadata["dxf_data"]["file_size_mb"] = round(file_size / (1024 * 1024), 2)
	except Exception:
		pass
	
	return metadata


def process_dwg(dwg_path: str, temp_dir: Optional[str] = None) -> Dict[str, Any]:
	"""Convert DWG→DXF via free tools and parse DXF via ezdxf."""
	out_dir = Path(temp_dir) if temp_dir else Path(dwg_path).parent / "_converted_dxf"
	
	# Try free alternatives first
	try:
		dxf_path = convert_dwg_to_dxf_via_libredwg(dwg_path, str(out_dir))
		logger.info("Using libredwg for DWG conversion")
	except Exception as e:
		logger.warning(f"libredwg conversion failed: {e}")
		try:
			dxf_path = convert_dwg_to_dxf_via_oda(dwg_path, str(out_dir))
			logger.info("Using ODA File Converter for DWG conversion")
		except Exception as e2:
			# Fallback to basic DWG metadata extraction
			logger.warning(f"All DWG conversion methods failed. libredwg: {e}, ODA: {e2}")
			return _extract_dwg_metadata_only(dwg_path)
	
	dxf_data = parse_dxf(dxf_path)
	return {
		"source": Path(dwg_path).name,
		"from_dwg": True,
		"dxf_path": dxf_path,
		"dxf_data": dxf_data,
	}


# ---------------------- IGES Handling ----------------------

def _shape_from_iges(iges_path: str) -> "TopoDS_Shape":
	reader = IGESControl_Reader()
	Interface_Static_SetCVal("xstep.cascade.unit", "MM")
	status = reader.ReadFile(iges_path)
	if status != 1:
		raise RuntimeError("IGES read failed")
	reader.TransferRoots()
	shape = reader.OneShape()
	return shape


def _bbox_of_shape(shape: "TopoDS_Shape") -> Tuple[float, float, float, float, float, float]:
	box = Bnd_Box()
	brepbndlib_Add(shape, box)
	xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
	return xmin, ymin, zmin, xmax, ymax, zmax


def _topology_counts(shape: "TopoDS_Shape") -> Tuple[int, int, int]:
	faces = 0
	edges = 0
	vertices = 0
	exp = TopExp_Explorer(shape, TopAbs_FACE)
	while exp.More():
		faces += 1
		exp.Next()
	exp = TopExp_Explorer(shape, TopAbs_EDGE)
	while exp.More():
		edges += 1
		exp.Next()
	exp = TopExp_Explorer(shape, TopAbs_VERTEX)
	while exp.More():
		vertices += 1
		exp.Next()
	return faces, edges, vertices


def _shape_properties(shape: "TopoDS_Shape") -> Dict[str, float]:
	props: Dict[str, float] = {}
	try:
		gp = GProp_GProps()
		brepgprop_VolumeProperties(shape, gp)
		props["volume"] = gp.Mass()
	except Exception:
		pass
	try:
		gp = GProp_GProps()
		brepgprop_SurfaceProperties(shape, gp)
		props["surface_area"] = gp.Mass()
	except Exception:
		pass
	return props


def process_iges(iges_path: str) -> Dict[str, Any]:
	if not OCCT_AVAILABLE:
		raise RuntimeError("pythonocc-core/OCP not installed. Install OCP or pythonocc-core.")

	shape = _shape_from_iges(iges_path)
	xmin, ymin, zmin, xmax, ymax, zmax = _bbox_of_shape(shape)
	faces, edges, vertices = _topology_counts(shape)
	props = _shape_properties(shape)

	result = {
		"bbox": {
			"xmin": xmin,
			"ymin": ymin,
			"zmin": zmin,
			"xmax": xmax,
			"ymax": ymax,
			"zmax": zmax,
		},
		"topology": {
			"faces": faces,
			"edges": edges,
			"vertices": vertices,
		},
		"properties": props,
	}
	return result


# ---------------------- Integration Helper ----------------------

def parse_cad(file_path: str) -> Dict[str, Any]:
	"""
	Unified entry point:
	- .dwg → convert & parse DXF
	- .dxf → parse DXF
	- .iges/.igs → parse IGES
	- .step/.stp → currently treated as text elsewhere; could be added here
	"""
	p = Path(file_path)
	ext = p.suffix.lower()
	if ext == ".dwg":
		return process_dwg(str(p))
	if ext == ".dxf":
		return {"source": p.name, "from_dwg": False, "dxf_data": parse_dxf(str(p))}
	if ext in (".iges", ".igs"):
		return {"source": p.name, "iges": process_iges(str(p))}
	raise ValueError(f"Unsupported CAD extension for parser: {ext}")


if __name__ == "__main__":
	import argparse
	ap = argparse.ArgumentParser(description="CAD Parser")
	ap.add_argument("path", help="Path to CAD file (.dwg/.dxf/.iges/.igs)")
	args = ap.parse_args()
	try:
		data = parse_cad(args.path)
		print(json.dumps(data, ensure_ascii=False, indent=2))
	except Exception as e:
		logger.exception("CAD parsing failed")
		raise SystemExit(1)



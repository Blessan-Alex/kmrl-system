"""
Enhanced CAD processor with DXF support
"""
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    logger.warning("ezdxf not available. Install with: pip install ezdxf")

from document_processor.models import FileType, ProcessingResult
from document_processor.processors.base_processor import BaseProcessor
from document_processor.utils.cad_converter import convert_dwg_to_dxf, find_dwg_converter

# Import the new cad_parser module
try:
    from cad_parser.processor import parse_cad
    CAD_PARSER_AVAILABLE = True
except ImportError:
    CAD_PARSER_AVAILABLE = False
    logger.warning("cad_parser module not available. Using basic CAD processing.")


class EnhancedCADProcessor(BaseProcessor):
    """Enhanced CAD processor with DXF extraction capabilities"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [FileType.CAD]
        self.cad_extensions = {
            '.dwg': 'AutoCAD Drawing',
            '.dxf': 'Drawing Exchange Format',
            '.step': 'STEP 3D Model',
            '.stp': 'STEP 3D Model',
            '.iges': 'IGES 3D Model',
            '.igs': 'IGES 3D Model'
        }
    
    def can_process(self, file_type: FileType) -> bool:
        """Check if processor can handle file type"""
        return file_type in self.supported_types
    
    def process(self, file_path: str, file_type: FileType, **kwargs) -> ProcessingResult:
        """Process CAD file with enhanced extraction"""
        start_time = time.time()
        file_id = kwargs.get('file_id', Path(file_path).stem)
        
        try:
            if not self.validate_file(file_path):
                return self.create_error_result(
                    file_id, f"Invalid file: {file_path}",
                    self.get_processing_time(start_time, time.time())
                )
            
            # Extract CAD data
            cad_data = self._extract_cad_data(file_path)
            
            # Generate comprehensive text
            extracted_text = self._generate_cad_text(file_path, cad_data)
            
            # Prepare metadata
            metadata = {
                'processor': 'enhanced_cad_processor',
                'file_type': 'cad',
                'cad_data': cad_data,
                'extraction_method': 'ezdxf' if file_path.lower().endswith('.dxf') and EZDXF_AVAILABLE else 'metadata_only',
                'ezdxf_available': EZDXF_AVAILABLE
            }
            
            processing_time = self.get_processing_time(start_time, time.time())
            
            return self.create_success_result(
                file_id, extracted_text, metadata, processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing CAD file {file_path}: {str(e)}")
            return self.create_error_result(
                file_id, f"CAD processing failed: {str(e)}",
                self.get_processing_time(start_time, time.time())
            )
    
    def _extract_cad_data(self, file_path: str) -> Dict[str, Any]:
        """Extract data from CAD file"""
        # Try the new cad_parser module first
        if CAD_PARSER_AVAILABLE:
            try:
                logger.info(f"Using cad_parser module for {file_path}")
                return parse_cad(file_path)
            except Exception as e:
                logger.warning(f"cad_parser failed for {file_path}: {e}")
                # Fall back to original method
                pass
        
        # Fallback to original extraction methods
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension == '.dxf' and EZDXF_AVAILABLE:
            return self._extract_dxf_data(file_path)
        elif extension == '.dwg':
            # Try DWG -> DXF conversion if possible
            try:
                tool_name, _ = find_dwg_converter()
                logger.info(f"DWG detected. Attempting conversion using {tool_name}")
                dxf_path = convert_dwg_to_dxf(str(file_path))
                return self._extract_dxf_data(Path(dxf_path))
            except Exception as e:
                logger.warning(f"DWG conversion unavailable/failed: {e}")
                return self._extract_metadata_only(file_path)
        else:
            return self._extract_metadata_only(file_path)
    
    def _extract_dxf_data(self, file_path: Path) -> Dict[str, Any]:
        """Extract data from DXF file using ezdxf"""
        try:
            doc = ezdxf.readfile(str(file_path))
            
            # Extract basic info
            data = {
                'dxf_version': doc.dxfversion,
                'layers': len(doc.layers),
                'blocks': len(doc.blocks),
                'entities': len(doc.modelspace()),
                'text_entities': 0,
                'dimensions': 0,
                'lines': 0,
                'circles': 0,
                'arcs': 0,
                'polylines': 0,
                'splines': 0,
                'hatches': 0
            }
            
            # Count entity types and extract text
            text_content = []
            layer_info = {}
            
            for entity in doc.modelspace():
                entity_type = entity.dxftype()
                
                # Count entity types
                if entity_type in ['TEXT', 'MTEXT']:
                    data['text_entities'] += 1
                    # Extract text content
                    if entity_type == 'TEXT':
                        text_content.append(entity.dxf.text)
                    elif entity_type == 'MTEXT':
                        text_content.append(entity.plain_text())
                        
                elif entity_type == 'DIMENSION':
                    data['dimensions'] += 1
                elif entity_type == 'LINE':
                    data['lines'] += 1
                elif entity_type == 'CIRCLE':
                    data['circles'] += 1
                elif entity_type == 'ARC':
                    data['arcs'] += 1
                elif entity_type == 'LWPOLYLINE':
                    data['polylines'] += 1
                elif entity_type == 'SPLINE':
                    data['splines'] += 1
                elif entity_type == 'HATCH':
                    data['hatches'] += 1
                
                # Collect layer information
                layer_name = getattr(entity.dxf, 'layer', '0')
                if layer_name not in layer_info:
                    layer_info[layer_name] = 0
                layer_info[layer_name] += 1
            
            data['text_content'] = text_content
            data['layer_info'] = layer_info
            data['extraction_successful'] = True
            
            return data
            
        except Exception as e:
            logger.warning(f"DXF extraction failed for {file_path}: {str(e)}")
            return self._extract_metadata_only(file_path)
    
    def _extract_metadata_only(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic metadata for unsupported formats"""
        stat = file_path.stat()
        return {
            'filename': file_path.name,
            'size': stat.st_size,
            'extension': file_path.suffix.lower(),
            'extraction_successful': False,
            'reason': 'Format not supported for detailed extraction'
        }
    
    def _generate_cad_text(self, file_path: str, cad_data: Dict[str, Any]) -> str:
        """Generate comprehensive text from CAD data"""
        file_name = Path(file_path).name
        
        if cad_data.get('extraction_successful'):
            # DXF file with extracted data
            text = f"""CAD Document: {file_name}
Format: Drawing Exchange Format (DXF)
Version: {cad_data.get('dxf_version', 'Unknown')}

Document Structure:
- Layers: {cad_data.get('layers', 0)}
- Blocks: {cad_data.get('blocks', 0)}
- Total Entities: {cad_data.get('entities', 0)}

Entity Breakdown:
- Text Entities: {cad_data.get('text_entities', 0)}
- Dimensions: {cad_data.get('dimensions', 0)}
- Lines: {cad_data.get('lines', 0)}
- Circles: {cad_data.get('circles', 0)}
- Arcs: {cad_data.get('arcs', 0)}
- Polylines: {cad_data.get('polylines', 0)}
- Splines: {cad_data.get('splines', 0)}
- Hatches: {cad_data.get('hatches', 0)}

Layer Information:
{self._format_layer_info(cad_data.get('layer_info', {}))}

Text Content:
{chr(10).join(cad_data.get('text_content', ['No text found']))}

Technical Details:
- File Size: {Path(file_path).stat().st_size / 1024:.1f} KB
- Processing Method: DXF Entity Extraction
- Viewer Recommendation: AutoCAD, FreeCAD, or online DXF viewers

This CAD file has been processed using enhanced extraction methods.
The document contains technical drawings with {cad_data.get('entities', 0)} entities
across {cad_data.get('layers', 0)} layers."""
        else:
            # Basic metadata only
            text = f"""CAD Document: {file_name}
Format: {cad_data.get('extension', 'Unknown').upper()}
File Size: {cad_data.get('size', 0) / 1024:.1f} KB

Note: This CAD file format requires specialized software for detailed processing.
The file contains technical drawings that cannot be directly converted to text.

Recommended Actions:
1. Use appropriate CAD software to open and view the file
2. Export to DXF format for enhanced processing
3. Use specialized CAD viewers for online viewing

File Details:
- Extension: {cad_data.get('extension', 'Unknown')}
- Size: {cad_data.get('size', 0)} bytes
- Processing: Metadata extraction only

This file has been processed by the KMRL Document Processing System
but requires specialized handling due to its technical nature."""
        
        return text
    
    def _format_layer_info(self, layer_info: Dict[str, int]) -> str:
        """Format layer information for display"""
        if not layer_info:
            return "No layer information available"
        
        lines = []
        for layer_name, count in sorted(layer_info.items()):
            lines.append(f"- {layer_name}: {count} entities")
        
        return '\n'.join(lines)
    
    def get_cad_summary(self, file_path: str) -> Dict[str, Any]:
        """Get a summary of CAD file contents"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {'error': 'File not found'}
            
            if file_path.suffix.lower() == '.dxf' and EZDXF_AVAILABLE:
                return self._get_dxf_summary(file_path)
            else:
                return self._get_basic_summary(file_path)
                
        except Exception as e:
            return {'error': str(e)}
    
    def _get_dxf_summary(self, file_path: Path) -> Dict[str, Any]:
        """Get DXF file summary"""
        try:
            doc = ezdxf.readfile(str(file_path))
            
            summary = {
                'file_name': file_path.name,
                'dxf_version': doc.dxfversion,
                'layers': len(doc.layers),
                'blocks': len(doc.blocks),
                'entities': len(doc.modelspace()),
                'has_text': False,
                'has_dimensions': False,
                'has_geometry': False
            }
            
            # Check for specific content types
            for entity in doc.modelspace():
                entity_type = entity.dxftype()
                if entity_type in ['TEXT', 'MTEXT']:
                    summary['has_text'] = True
                elif entity_type == 'DIMENSION':
                    summary['has_dimensions'] = True
                elif entity_type in ['LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE']:
                    summary['has_geometry'] = True
            
            return summary
            
        except Exception as e:
            return {'error': f'DXF processing failed: {str(e)}'}
    
    def _get_basic_summary(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file summary"""
        stat = file_path.stat()
        return {
            'file_name': file_path.name,
            'size': stat.st_size,
            'extension': file_path.suffix.lower(),
            'format': self.cad_extensions.get(file_path.suffix.lower(), 'Unknown'),
            'processing_available': False
        }


"""
CAD document processor for technical drawings
"""
import time
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from document_processor.models import FileType, ProcessingResult
from document_processor.processors.base_processor import BaseProcessor


class CADProcessor(BaseProcessor):
    """Processor for CAD and technical drawing files"""
    
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
        """Process CAD document"""
        start_time = time.time()
        file_id = kwargs.get('file_id', Path(file_path).stem)
        
        try:
            if not self.validate_file(file_path):
                return self.create_error_result(
                    file_id, f"Invalid file: {file_path}",
                    self.get_processing_time(start_time, time.time())
                )
            
            # Extract metadata from CAD file
            metadata = self._extract_cad_metadata(file_path)
            
            # Create placeholder text for CAD files
            placeholder_text = self._create_placeholder_text(file_path, metadata)
            
            processing_time = self.get_processing_time(start_time, time.time())
            
            return self.create_success_result(
                file_id, placeholder_text, metadata, processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing CAD file {file_path}: {str(e)}")
            return self.create_error_result(
                file_id, f"CAD processing failed: {str(e)}",
                self.get_processing_time(start_time, time.time())
            )
    
    def _extract_cad_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from CAD file"""
        try:
            file_path = Path(file_path)
            file_size = file_path.stat().st_size
            extension = file_path.suffix.lower()
            
            metadata = {
                'processor': 'cad_processor',
                'file_type': 'cad',
                'cad_format': self.cad_extensions.get(extension, 'Unknown CAD Format'),
                'file_extension': extension,
                'file_size': file_size,
                'requires_specialized_viewer': True,
                'processing_note': 'CAD file - requires specialized viewer for full content access'
            }
            
            # Add format-specific metadata
            if extension in ['.dwg', '.dxf']:
                metadata.update({
                    'format_category': '2D_Drawing',
                    'viewer_recommendation': 'AutoCAD, FreeCAD, or online DWG viewers'
                })
            elif extension in ['.step', '.stp', '.iges', '.igs']:
                metadata.update({
                    'format_category': '3D_Model',
                    'viewer_recommendation': 'FreeCAD, OpenCASCADE, or 3D viewers'
                })
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Metadata extraction failed for {file_path}: {str(e)}")
            return {
                'processor': 'cad_processor',
                'file_type': 'cad',
                'error': str(e)
            }
    
    def _create_placeholder_text(self, file_path: str, metadata: Dict[str, Any]) -> str:
        """Create placeholder text for CAD files"""
        file_name = Path(file_path).name
        cad_format = metadata.get('cad_format', 'CAD File')
        file_size = metadata.get('file_size', 0)
        
        # Format file size
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} bytes"
        
        placeholder_text = f"""
CAD Document: {file_name}
Format: {cad_format}
File Size: {size_str}
Category: {metadata.get('format_category', 'Technical Drawing')}

Note: This is a CAD/technical drawing file that requires specialized software to view and edit.
The file contains technical drawings, 3D models, or engineering data that cannot be directly
converted to text format.

Recommended Actions:
1. Use appropriate CAD software to open and view the file
2. Export to PDF or image format if text extraction is needed
3. Use specialized CAD viewers for online viewing

File Details:
- Extension: {metadata.get('file_extension', 'Unknown')}
- Requires Specialized Viewer: Yes
- Viewer Recommendation: {metadata.get('viewer_recommendation', 'CAD software')}

This file has been processed by the KMRL Document Processing System but requires
specialized handling due to its technical nature.
        """.strip()
        
        return placeholder_text
    
    def get_cad_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed information about CAD file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {'error': 'File not found'}
            
            # Basic file information
            stat = file_path.stat()
            
            info = {
                'filename': file_path.name,
                'extension': file_path.suffix.lower(),
                'size_bytes': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'cad_format': self.cad_extensions.get(file_path.suffix.lower(), 'Unknown'),
                'is_cad_file': file_path.suffix.lower() in self.cad_extensions
            }
            
            # Add format-specific information
            extension = file_path.suffix.lower()
            if extension in ['.dwg', '.dxf']:
                info['category'] = '2D_Drawing'
                info['description'] = 'AutoCAD drawing file'
            elif extension in ['.step', '.stp']:
                info['category'] = '3D_Model'
                info['description'] = 'STEP 3D model file'
            elif extension in ['.iges', '.igs']:
                info['category'] = '3D_Model'
                info['description'] = 'IGES 3D model file'
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting CAD info for {file_path}: {str(e)}")
            return {'error': str(e)}
    
    def validate_cad_file(self, file_path: str) -> Dict[str, Any]:
        """Validate CAD file and return validation results"""
        try:
            file_path = Path(file_path)
            
            validation_result = {
                'is_valid': False,
                'errors': [],
                'warnings': [],
                'file_info': {}
            }
            
            # Check if file exists
            if not file_path.exists():
                validation_result['errors'].append('File does not exist')
                return validation_result
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size == 0:
                validation_result['errors'].append('File is empty')
                return validation_result
            
            # Check file extension
            extension = file_path.suffix.lower()
            if extension not in self.cad_extensions:
                validation_result['errors'].append(f'Unsupported CAD format: {extension}')
                return validation_result
            
            # File appears to be valid
            validation_result['is_valid'] = True
            validation_result['file_info'] = {
                'filename': file_path.name,
                'extension': extension,
                'size': file_size,
                'format': self.cad_extensions[extension]
            }
            
            # Add warnings for large files
            if file_size > 50 * 1024 * 1024:  # 50MB
                validation_result['warnings'].append('Large file size may cause processing delays')
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating CAD file {file_path}: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f'Validation failed: {str(e)}'],
                'warnings': [],
                'file_info': {}
            }

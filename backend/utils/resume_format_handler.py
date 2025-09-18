"""
Resume Format Handler for Advanced Resume Parser
Supports PDF, DOCX, and TXT resume formats
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ResumeFormatHandler:
    """Handler for different resume file formats"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt']
    
    def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """
        Extract text content from resume file
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.txt':
                return self._extract_from_txt(file_path)
            elif file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            else:
                logger.error(f"Unsupported file format: {file_extension}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text from file {file_path}: {str(e)}")
            return None
    
    def _extract_from_txt(self, file_path: Path) -> Optional[str]:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Error reading TXT file with latin-1 encoding: {e}")
                return None
        except Exception as e:
            logger.error(f"Error reading TXT file: {e}")
            return None
    
    def _extract_from_pdf(self, file_path: Path) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            # Try to import PyPDF2 or pdfplumber
            try:
                import PyPDF2
                return self._extract_pdf_pypdf2(file_path)
            except ImportError:
                try:
                    import pdfplumber
                    return self._extract_pdf_pdfplumber(file_path)
                except ImportError:
                    logger.error("No PDF extraction library available. Install PyPDF2 or pdfplumber.")
                    return None
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return None
    
    def _extract_pdf_pypdf2(self, file_path: Path) -> Optional[str]:
        """Extract text using PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF with PyPDF2: {e}")
            return None
    
    def _extract_pdf_pdfplumber(self, file_path: Path) -> Optional[str]:
        """Extract text using pdfplumber"""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF with pdfplumber: {e}")
            return None
    
    def _extract_from_docx(self, file_path: Path) -> Optional[str]:
        """Extract text from DOCX file"""
        try:
            # Try to import python-docx
            try:
                from docx import Document
                return self._extract_docx_python_docx(file_path)
            except ImportError:
                logger.error("python-docx library not available. Install with: pip install python-docx")
                return None
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return None
    
    def _extract_docx_python_docx(self, file_path: Path) -> Optional[str]:
        """Extract text using python-docx"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX with python-docx: {e}")
            return None
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported"""
        try:
            file_extension = Path(file_path).suffix.lower()
            return file_extension in self.supported_formats
        except Exception:
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {'error': 'File not found'}
            
            stat = file_path.stat()
            return {
                'file_name': file_path.name,
                'file_size': stat.st_size,
                'file_extension': file_path.suffix.lower(),
                'is_supported': self.is_supported_format(str(file_path)),
                'modified_time': stat.st_mtime
            }
        except Exception as e:
            return {'error': str(e)}

# Enhanced AdvancedResumeParser with format support
class AdvancedResumeParserWithFormats(AdvancedResumeParser):
    """Advanced Resume Parser with file format support"""
    
    def __init__(self):
        super().__init__()
        self.format_handler = ResumeFormatHandler()
    
    def parse_resume_file(self, file_path: str, location: str = "New York") -> Dict[str, Any]:
        """
        Parse resume from file with advanced analytics
        
        Args:
            file_path: Path to the resume file
            location: Location for income potential calculation
            
        Returns:
            Dictionary containing parsed resume data and advanced analytics
        """
        try:
            # Check if file format is supported
            if not self.format_handler.is_supported_format(file_path):
                return {
                    'success': False,
                    'error': f'Unsupported file format. Supported formats: {self.format_handler.supported_formats}',
                    'parsed_data': {},
                    'advanced_analytics': {}
                }
            
            # Get file info
            file_info = self.format_handler.get_file_info(file_path)
            if 'error' in file_info:
                return {
                    'success': False,
                    'error': f'Error getting file info: {file_info["error"]}',
                    'parsed_data': {},
                    'advanced_analytics': {}
                }
            
            # Extract text from file
            content = self.format_handler.extract_text_from_file(file_path)
            if not content:
                return {
                    'success': False,
                    'error': 'Failed to extract text from file',
                    'parsed_data': {},
                    'advanced_analytics': {}
                }
            
            # Parse with advanced analytics
            result = self.parse_resume_advanced(
                content=content,
                file_name=file_info['file_name'],
                location=location
            )
            
            # Add file information to result
            if result.get('success', False):
                result['file_info'] = file_info
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing resume file {file_path}: {str(e)}")
            return {
                'success': False,
                'error': f'Error parsing file: {str(e)}',
                'parsed_data': {},
                'advanced_analytics': {}
            }
    
    def parse_resume_from_bytes(self, file_bytes: bytes, file_name: str, location: str = "New York") -> Dict[str, Any]:
        """
        Parse resume from file bytes with advanced analytics
        
        Args:
            file_bytes: File content as bytes
            file_name: Original file name
            location: Location for income potential calculation
            
        Returns:
            Dictionary containing parsed resume data and advanced analytics
        """
        try:
            # Check if file format is supported
            if not self.format_handler.is_supported_format(file_name):
                return {
                    'success': False,
                    'error': f'Unsupported file format. Supported formats: {self.format_handler.supported_formats}',
                    'parsed_data': {},
                    'advanced_analytics': {}
                }
            
            # Create temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_name).suffix) as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name
            
            try:
                # Parse the temporary file
                result = self.parse_resume_file(temp_file_path, location)
                
                # Add file information
                if result.get('success', False):
                    result['file_info'] = {
                        'file_name': file_name,
                        'file_size': len(file_bytes),
                        'file_extension': Path(file_name).suffix.lower(),
                        'is_supported': True
                    }
                
                return result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Error deleting temporary file: {e}")
            
        except Exception as e:
            logger.error(f"Error parsing resume from bytes: {str(e)}")
            return {
                'success': False,
                'error': f'Error parsing file bytes: {str(e)}',
                'parsed_data': {},
                'advanced_analytics': {}
            }

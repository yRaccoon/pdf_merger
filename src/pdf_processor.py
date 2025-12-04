from pypdf import PdfReader, PdfWriter, PasswordType
from .utils.page_range import PageRangeParser
import os

class PDFProcessor:
    """Handles PDF merging and processing operations with advanced features"""
    
    def merge_pdfs(self, input_paths, output_path, file_settings=None):
        """
        Merge multiple PDF files into a single PDF with advanced options
        
        Args:
            input_paths: List of paths to input PDF files
            output_path: Path for the output merged PDF
            file_settings: Dict of {index: {'range': str, 'password': str}}
        
        Returns:
            Tuple (success: bool, message: str)
        """
        if not input_paths:
            return False, "No input files provided"
        
        if file_settings is None:
            file_settings = {}
        
        writer = PdfWriter()
        processed_count = 0
        total_pages = 0
        
        try:
            for i, pdf_path in enumerate(input_paths):
                if not os.path.exists(pdf_path):
                    return False, f"File not found: {pdf_path}"
                
                try:
                    # Get settings for this file
                    settings = file_settings.get(i, {})
                    page_range_str = settings.get('range', '')
                    password = settings.get('password', '')
                    
                    # Open PDF with password if provided
                    reader = self.open_pdf_with_password(pdf_path, password)
                    if isinstance(reader, str):  # Error message
                        return False, f"File {os.path.basename(pdf_path)}: {reader}"
                    
                    # Get page numbers to include
                    page_numbers = self.get_pages_to_include(reader, page_range_str)
                    if isinstance(page_numbers, str):  # Error message
                        return False, f"File {os.path.basename(pdf_path)}: {page_numbers}"
                    
                    # Add selected pages to writer
                    for page_num in page_numbers:
                        # Convert to 0-based index for pypdf
                        page = reader.pages[page_num - 1]
                        writer.add_page(page)
                    
                    total_pages += len(page_numbers)
                    processed_count += 1
                        
                except Exception as e:
                    return False, f"Error processing {os.path.basename(pdf_path)}: {str(e)}"
            
            # Write to output file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True, f"Successfully merged {processed_count} files ({total_pages} pages)"
            
        except Exception as e:
            return False, f"Merge failed: {str(e)}"
    
    def open_pdf_with_password(self, pdf_path, password=None):
        """
        Open a PDF file, handling encryption if needed
        
        Args:
            pdf_path: Path to PDF file
            password: Password for encrypted PDF (optional)
        
        Returns:
            PdfReader object or error message string
        """
        try:
            reader = PdfReader(pdf_path)
            
            # Check if PDF is encrypted
            if reader.is_encrypted:
                if password:
                    # Try to decrypt with provided password
                    if reader.decrypt(password) == PasswordType.NOT_DECRYPTED:
                        return "Incorrect password"
                else:
                    return "PDF is password protected. Please provide a password."
            
            return reader
            
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def get_pages_to_include(self, reader, page_range_str):
        """
        Get list of page numbers to include based on range string
        
        Args:
            reader: PdfReader object
            page_range_str: Page range string (e.g., "1,3,5-8")
        
        Returns:
            List of page numbers or error message string
        """
        total_pages = len(reader.pages)
        
        if not page_range_str.strip():
            # Include all pages
            return list(range(1, total_pages + 1))
        
        # Parse page range
        success, page_numbers, error = PageRangeParser.parse_range(page_range_str, total_pages)
        
        if not success:
            return error
        
        return page_numbers
    
    def validate_pdf(self, file_path, password=None):
        """Validate if a file is a readable PDF, optionally with password"""
        try:
            reader = self.open_pdf_with_password(file_path, password)
            if isinstance(reader, str):  # Error message
                return False, reader
            
            page_count = len(reader.pages)
            return True, f"Valid PDF ({page_count} pages)"
            
        except Exception as e:
            return False, str(e)
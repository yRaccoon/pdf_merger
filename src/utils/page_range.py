# src/utils/page_range.py - Page range parsing and validation
import re
from typing import List, Tuple

class PageRangeParser:
    """Parses and validates page range strings like '1,3,5-8'"""
    
    @staticmethod
    def parse_range(range_str: str, total_pages: int) -> Tuple[bool, List[int], str]:
        """
        Parse a page range string and validate against total pages
        
        Args:
            range_str: Page range string (e.g., "1,3,5-8")
            total_pages: Total number of pages in PDF
        
        Returns:
            Tuple (success, page_numbers, error_message)
        """
        if not range_str.strip():
            return True, list(range(1, total_pages + 1)), ""
        
        range_str = range_str.strip()
        page_numbers = []
        
        # Validate format
        if not re.match(r'^[\d\s,\-]+$', range_str):
            return False, [], "Invalid characters in page range"
        
        # Split by comma
        parts = [part.strip() for part in range_str.split(',') if part.strip()]
        
        for part in parts:
            if '-' in part:
                # Handle page range (e.g., "5-8")
                range_parts = part.split('-')
                if len(range_parts) != 2:
                    return False, [], f"Invalid range format: {part}"
                
                try:
                    start = int(range_parts[0])
                    end = int(range_parts[1])
                except ValueError:
                    return False, [], f"Invalid numbers in range: {part}"
                
                if start < 1:
                    return False, [], f"Start page must be >= 1: {part}"
                if end > total_pages:
                    return False, [], f"End page ({end}) exceeds total pages ({total_pages})"
                if start > end:
                    return False, [], f"Start page ({start}) > end page ({end})"
                
                page_numbers.extend(range(start, end + 1))
            else:
                # Handle single page
                try:
                    page = int(part)
                except ValueError:
                    return False, [], f"Invalid page number: {part}"
                
                if page < 1:
                    return False, [], f"Page number must be >= 1: {page}"
                if page > total_pages:
                    return False, [], f"Page {page} exceeds total pages ({total_pages})"
                
                page_numbers.append(page)
        
        # Remove duplicates and sort
        page_numbers = sorted(set(page_numbers))
        
        # Validate we have at least one page
        if not page_numbers:
            return False, [], "No valid pages specified"
        
        return True, page_numbers, ""
    
    @staticmethod
    def format_page_numbers(page_numbers: List[int]) -> str:
        """
        Format a list of page numbers into a compact range string
        
        Args:
            page_numbers: Sorted list of page numbers
        
        Returns:
            Formatted range string (e.g., "1,3,5-8")
        """
        if not page_numbers:
            return ""
        
        page_numbers = sorted(set(page_numbers))
        ranges = []
        start = page_numbers[0]
        end = page_numbers[0]
        
        for page in page_numbers[1:]:
            if page == end + 1:
                end = page
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = page
                end = page
        
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ",".join(ranges)
    
    @staticmethod
    def get_page_count(range_str: str, total_pages: int) -> int:
        """
        Get the number of pages in a range string
        
        Args:
            range_str: Page range string
            total_pages: Total pages in PDF
        
        Returns:
            Number of pages in range, or total_pages if invalid/empty
        """
        success, page_numbers, _ = PageRangeParser.parse_range(range_str, total_pages)
        if success:
            return len(page_numbers)
        return total_pages
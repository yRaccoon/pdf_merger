import fitz  # PyMuPDF
from PIL import Image, ImageFilter
import customtkinter as ctk
import os
import threading
import queue
from pathlib import Path
import shutil
import io
from PIL import ImageDraw, ImageFont

class PreviewManager:
    """Manages PDF preview generation and caching"""
    
    def __init__(self, cache_dir=None):
        # Set up cache directory
        if cache_dir is None:
            self.cache_dir = Path.home() / ".pdf_merger" / "preview_cache"
        else:
            self.cache_dir = Path(cache_dir)
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread-safe queue for async operations
        self.preview_queue = queue.Queue()
        self.is_processing = False
        
        # Cache for loaded previews
        self.thumbnail_cache = {}
        self.detailed_cache = {}
        
        # Max image dimensions to prevent decompression bomb
        self.max_image_size = (2000, 2000)
        
        # Start background thread
        self.start_background_processor()
    
    def start_background_processor(self):
        """Start background thread for preview generation"""
        self.background_thread = threading.Thread(
            target=self.process_queue,
            daemon=True
        )
        self.background_thread.start()
    
    def process_queue(self):
        """Process preview generation requests from queue"""
        while True:
            try:
                task = self.preview_queue.get()
                if task is None:  # Sentinel to stop
                    break
                
                func, args, callback = task
                result = func(*args)
                if callback:
                    callback(result)
                
                self.preview_queue.task_done()
                
            except Exception as e:
                print(f"Error in preview processor: {e}")
    
    def get_thumbnail(self, pdf_path, size=(100, 130), callback=None):
        """
        Get thumbnail for PDF (first page)
        
        Args:
            pdf_path: Path to PDF file
            size: Thumbnail size (width, height)
            callback: Function to call with result
        
        Returns:
            CTkImage if available synchronously, else None
        """
        # Check cache first
        cache_key = f"{pdf_path}_{size[0]}_{size[1]}"
        if cache_key in self.thumbnail_cache:
            if callback:
                callback(self.thumbnail_cache[cache_key])
            return self.thumbnail_cache[cache_key]
        
        # Check disk cache
        cached_path = self.cache_dir / f"{Path(pdf_path).stem}_{size[0]}x{size[1]}.png"
        if cached_path.exists():
            try:
                img = Image.open(cached_path)
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                self.thumbnail_cache[cache_key] = ctk_image
                if callback:
                    callback(ctk_image)
                return ctk_image
            except:
                pass
        
        # Queue for async generation
        self.preview_queue.put((
            self._generate_thumbnail,
            (pdf_path, size, cached_path, cache_key),
            callback
        ))
        
        return None
    
    def _generate_thumbnail(self, pdf_path, size, cache_path, cache_key):
        """Generate thumbnail image from PDF first page"""
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Get first page
            page = doc[0]
            
            # Calculate zoom factor for desired size with safety limits
            page_width = page.rect.width
            page_height = page.rect.height
            
            # Limit maximum dimensions to prevent huge images
            max_original_size = 5000  # Max 5000 pixels on either dimension
            if page_width > max_original_size or page_height > max_original_size:
                scale_factor = max_original_size / max(page_width, page_height)
                page_width *= scale_factor
                page_height *= scale_factor
            
            zoom_x = size[0] / page_width
            zoom_y = size[1] / page_height
            zoom = min(zoom_x, zoom_y) * 72  # 72 DPI
            
            # Further limit zoom to prevent huge images
            max_zoom = 4.0  # Max 4x zoom
            zoom = min(zoom, max_zoom * 72)
            
            # Render page to image
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Limit output size
            if pix.width > self.max_image_size[0] or pix.height > self.max_image_size[1]:
                scale = min(self.max_image_size[0] / pix.width, 
                           self.max_image_size[1] / pix.height)
                mat = fitz.Matrix(zoom * scale, zoom * scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to exact dimensions if needed
            if img.size != size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            
            # Add border and background
            final_img = Image.new('RGB', size, color='white')
            final_img.paste(img, (
                (size[0] - img.width) // 2,
                (size[1] - img.height) // 2
            ))
            
            # Add subtle shadow effect (lighter to reduce processing)
            shadow_img = Image.new('RGBA', (size[0] + 2, size[1] + 2), (0, 0, 0, 0))
            
            # Simple border instead of heavy shadow
            from PIL import ImageDraw
            draw = ImageDraw.Draw(final_img)
            draw.rectangle([0, 0, size[0]-1, size[1]-1], outline=(200, 200, 200), width=1)
            
            # Save to cache
            final_img.save(cache_path, 'PNG', optimize=True)
            
            # Create CTkImage
            ctk_image = ctk.CTkImage(
                light_image=final_img,
                dark_image=final_img,
                size=size
            )
            
            # Store in memory cache
            self.thumbnail_cache[cache_key] = ctk_image
            
            doc.close()
            return ctk_image
            
        except Exception as e:
            print(f"Error generating thumbnail for {pdf_path}: {e}")
            # Return a placeholder image
            return self._create_placeholder_thumbnail(size)
    
    def get_detailed_preview(self, pdf_path, max_pages=5, size=(400, 500), callback=None):
        """
        Get detailed preview of multiple pages
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to preview
            size: Size for each page preview
            callback: Function to call with result
        
        Returns:
            List of CTkImages if available synchronously, else None
        """
        cache_key = f"{pdf_path}_detailed_{max_pages}_{size[0]}_{size[1]}"
        if cache_key in self.detailed_cache:
            if callback:
                callback(self.detailed_cache[cache_key])
            return self.detailed_cache[cache_key]
        
        # Queue for async generation
        self.preview_queue.put((
            self._generate_detailed_preview,
            (pdf_path, max_pages, size, cache_key),
            callback
        ))
        
        return None
    
    def _generate_detailed_preview(self, pdf_path, max_pages, size, cache_key):
        """Generate detailed preview of multiple pages"""
        try:
            doc = fitz.open(pdf_path)
            page_count = min(len(doc), max_pages)
            previews = []
            
            for page_num in range(page_count):
                page = doc[page_num]
                
                # Calculate zoom factor with limits
                page_width = page.rect.width
                page_height = page.rect.height
                
                # Limit maximum dimensions
                max_original_size = 5000
                if page_width > max_original_size or page_height > max_original_size:
                    scale_factor = max_original_size / max(page_width, page_height)
                    page_width *= scale_factor
                    page_height *= scale_factor
                
                zoom_x = size[0] / page_width
                zoom_y = size[1] / page_height
                zoom = min(zoom_x, zoom_y) * 72
                
                # Limit zoom
                max_zoom = 2.0
                zoom = min(zoom, max_zoom * 72)
                
                # Render page
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Limit output size
                if pix.width > self.max_image_size[0] or pix.height > self.max_image_size[1]:
                    scale = min(self.max_image_size[0] / pix.width, 
                               self.max_image_size[1] / pix.height)
                    mat = fitz.Matrix(zoom * scale, zoom * scale)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert to PIL Image
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if needed
                if img.size != size:
                    img = img.resize(size, Image.Resampling.LANCZOS)
                
                # Add page number (simpler version)
                draw = ImageDraw.Draw(img)
                
                # Try to load font, fallback to default
                try:
                    font = ImageFont.truetype("arial.ttf", 12)
                except:
                    # Use default font
                    font = ImageFont.load_default()
                    # Scale default font
                    font = ImageFont.load_default()
                    if hasattr(font, 'getsize'):
                        # Older PIL
                        pass
                    else:
                        # Newer PIL
                        try:
                            font = ImageFont.truetype("arial.ttf", 12)
                        except:
                            pass
                
                # Draw page number in corner
                text = f"{page_num + 1}"
                text_color = (0, 0, 0)  # Black text
                bg_color = (255, 255, 255, 200)  # Semi-transparent white
                
                # Get text size
                try:
                    if hasattr(font, 'getsize'):
                        text_size = font.getsize(text)
                    else:
                        # PIL 9.0.0+
                        left, top, right, bottom = font.getbbox(text)
                        text_size = (right - left, bottom - top)
                except:
                    text_size = (20, 12)  # Fallback size
                
                # Draw background
                padding = 3
                bg_box = [
                    size[0] - text_size[0] - padding * 2 - 5,
                    size[1] - text_size[1] - padding * 2 - 5,
                    size[0] - 5,
                    size[1] - 5
                ]
                
                # Create a separate image for the background
                bg_img = Image.new('RGBA', (text_size[0] + padding * 2, text_size[1] + padding * 2), bg_color)
                text_img = Image.new('RGBA', bg_img.size, (255, 255, 255, 0))
                text_draw = ImageDraw.Draw(text_img)
                
                # Draw text on the separate image
                text_draw.text((padding, padding), text, font=font, fill=text_color)
                
                # Combine with main image
                img.paste(bg_img, (bg_box[0], bg_box[1]), bg_img)
                img.paste(text_img, (bg_box[0], bg_box[1]), text_img)
                
                # Create CTkImage
                ctk_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=size
                )
                previews.append(ctk_image)
            
            doc.close()
            
            # Cache result
            self.detailed_cache[cache_key] = previews
            return previews
            
        except Exception as e:
            print(f"Error generating detailed preview for {pdf_path}: {e}")
            return [self._create_placeholder_thumbnail(size)]
    
    def _create_placeholder_thumbnail(self, size):
        """Create a placeholder thumbnail when PDF can't be read"""
        img = Image.new('RGB', size, color=(240, 240, 240))
        
        draw = ImageDraw.Draw(img)
        
        # Draw simple PDF icon
        center_x, center_y = size[0] // 2, size[1] // 2
        
        # Draw document outline
        doc_width = min(40, size[0] // 3)
        doc_height = min(50, size[1] // 3)
        
        # Document body
        draw.rectangle([
            center_x - doc_width // 2,
            center_y - doc_height // 2,
            center_x + doc_width // 2,
            center_y + doc_height // 2
        ], fill=(220, 220, 220), outline=(180, 180, 180), width=1)
        
        # Document fold
        draw.polygon([
            (center_x - doc_width // 2, center_y - doc_height // 2),
            (center_x - doc_width // 2 + 10, center_y - doc_height // 2),
            (center_x - doc_width // 2, center_y - doc_height // 2 + 10)
        ], fill=(200, 200, 200))
        
        # Text
        try:
            # Try to use default font
            font = ImageFont.load_default()
            if hasattr(font, 'getsize'):
                text = "PDF"
                text_size = font.getsize(text)
                draw.text(
                    (center_x - text_size[0] // 2, center_y + doc_height // 2 + 5),
                    text,
                    font=font,
                    fill=(150, 150, 150)
                )
        except:
            pass
        
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    
    def clear_cache(self):
        """Clear all cached previews"""
        self.thumbnail_cache.clear()
        self.detailed_cache.clear()
        
        # Clear disk cache
        if self.cache_dir.exists():
            try:
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            except:
                pass
    
    def cleanup(self):
        """Cleanup resources"""
        self.preview_queue.put(None)  # Signal thread to stop
import customtkinter as ctk
from PIL import Image
import os

class PreviewPane(ctk.CTkFrame):
    """Detailed PDF preview panel showing multiple pages"""
    
    def __init__(self, master, preview_manager, **kwargs):
        super().__init__(master, **kwargs)
        
        self.preview_manager = preview_manager
        self.current_pdf = None
        self.previews = []
        self.current_page = 0
        self.preview_widgets = []  # Track preview widgets
        
        self.setup_ui()
        self.show_placeholder()
    
    def setup_ui(self):
        """Setup the preview panel UI"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with PDF info
        self.header_frame = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.pdf_title = ctk.CTkLabel(
            self.header_frame,
            text="PDF Preview",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.pdf_title.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.page_info = ctk.CTkLabel(
            self.header_frame,
            text="",
            text_color="gray"
        )
        self.page_info.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        
        # Preview area (scrollable)
        self.preview_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.preview_scroll.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.preview_scroll.grid_columnconfigure(0, weight=1)
        
        # Placeholder
        self.placeholder_frame = ctk.CTkFrame(self.preview_scroll, fg_color="transparent")
        self.placeholder_frame.grid(row=0, column=0, padx=20, pady=50, sticky="nsew")
        self.placeholder_frame.grid_columnconfigure(0, weight=1)
        
        self.placeholder_label = ctk.CTkLabel(
            self.placeholder_frame,
            text="👈 Select a PDF file to preview",
            font=ctk.CTkFont(size=18),
            text_color="gray"
        )
        self.placeholder_label.grid(row=0, column=0, pady=20)
        
        self.placeholder_hint = ctk.CTkLabel(
            self.placeholder_frame,
            text="Click on any file in the list to see its preview here",
            text_color="gray"
        )
        self.placeholder_hint.grid(row=1, column=0)
    
    def clear_preview_widgets(self):
        """Safely clear all preview widgets"""
        for widget in self.preview_widgets:
            try:
                widget.destroy()
            except:
                pass
        self.preview_widgets.clear()
    
    def show_placeholder(self):
        """Show placeholder when no PDF is selected"""
        self.clear_preview_widgets()
        self.placeholder_frame.grid()
        self.pdf_title.configure(text="PDF Preview")
        self.page_info.configure(text="")
        self.previews = []
        self.current_pdf = None
    
    def show_pdf_preview(self, pdf_path):
        """Show preview for a specific PDF"""
        # Don't reload if same PDF
        if self.current_pdf == pdf_path:
            return
            
        self.current_pdf = pdf_path
        self.placeholder_frame.grid_remove()
        
        # Update title
        file_name = os.path.basename(pdf_path)
        self.pdf_title.configure(text=f"Preview: {file_name}")
        
        # Show loading state
        self.show_loading()
        
        # Request detailed preview
        self.preview_manager.get_detailed_preview(
            pdf_path,
            max_pages=5,
            size=(350, 450),
            callback=self.display_previews
        )
    
    def show_loading(self):
        """Show loading state"""
        self.clear_preview_widgets()
        
        loading_frame = ctk.CTkFrame(self.preview_scroll, fg_color="transparent")
        loading_frame.grid(row=0, column=0, padx=20, pady=50, sticky="nsew")
        loading_frame.grid_columnconfigure(0, weight=1)
        
        loading_label = ctk.CTkLabel(
            loading_frame,
            text="Generating preview...",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        loading_label.grid(row=0, column=0, pady=10)
        
        progress_bar = ctk.CTkProgressBar(loading_frame, width=200, mode="indeterminate")
        progress_bar.grid(row=1, column=0, pady=10)
        progress_bar.start()
        
        self.preview_widgets.extend([loading_frame, loading_label, progress_bar])
    
    def display_previews(self, previews):
        """Display the generated previews"""
        if not previews:
            self.show_error("Could not generate preview")
            return
        
        self.previews = previews
        self.clear_preview_widgets()
        
        # Display each page preview
        for i, preview_image in enumerate(previews):
            page_frame = ctk.CTkFrame(self.preview_scroll, corner_radius=8)
            page_frame.grid(row=i, column=0, padx=10, pady=10, sticky="ew")
            page_frame.grid_columnconfigure(0, weight=1)
            
            # Page label
            page_label = ctk.CTkLabel(
                page_frame,
                text=f"Page {i + 1}",
                font=ctk.CTkFont(weight="bold")
            )
            page_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
            
            # Preview image
            image_label = ctk.CTkLabel(
                page_frame,
                image=preview_image,
                text=""
            )
            image_label.grid(row=1, column=0, padx=10, pady=(0, 10))
            
            # Add subtle border
            page_frame.configure(border_width=1, border_color=("gray80", "gray30"))
            
            self.preview_widgets.extend([page_frame, page_label, image_label])
        
        # Update page info
        try:
            import fitz
            doc = fitz.open(self.current_pdf)
            total_pages = len(doc)
            shown_pages = len(previews)
            doc.close()
            
            if shown_pages < total_pages:
                self.page_info.configure(
                    text=f"Showing {shown_pages} of {total_pages} pages"
                )
            else:
                self.page_info.configure(
                    text=f"{total_pages} page{'s' if total_pages != 1 else ''}"
                )
        except:
            self.page_info.configure(text=f"{len(previews)} pages shown")
    
    def show_error(self, message):
        """Show error message"""
        self.clear_preview_widgets()
        
        error_frame = ctk.CTkFrame(self.preview_scroll, fg_color="transparent")
        error_frame.grid(row=0, column=0, padx=20, pady=50, sticky="nsew")
        error_frame.grid_columnconfigure(0, weight=1)
        
        error_label = ctk.CTkLabel(
            error_frame,
            text="⚠️ Could not load preview",
            font=ctk.CTkFont(size=14),
            text_color="orange"
        )
        error_label.grid(row=0, column=0, pady=10)
        
        detail_label = ctk.CTkLabel(
            error_frame,
            text=message,
            text_color="gray",
            wraplength=300
        )
        detail_label.grid(row=1, column=0, pady=5)
        
        self.preview_widgets.extend([error_frame, error_label, detail_label])
    
    def clear_preview(self):
        """Clear current preview"""
        self.current_pdf = None
        self.previews = []
        self.show_placeholder()
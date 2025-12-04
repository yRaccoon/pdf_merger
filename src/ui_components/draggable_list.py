import customtkinter as ctk
import os
from datetime import datetime
from pathlib import Path

class DraggableFileFrame(ctk.CTkFrame):
    """A draggable frame representing a PDF file with settings and move buttons"""
    
    def __init__(self, master, file_path, index, total_files, preview_manager, 
                 remove_callback, drag_start_callback, drag_end_callback, 
                 move_up_callback, move_down_callback,
                 settings_callback=None, select_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.file_path = file_path
        self.index = index
        self.total_files = total_files
        self.preview_manager = preview_manager
        self.remove_callback = remove_callback
        self.drag_start_callback = drag_start_callback
        self.drag_end_callback = drag_end_callback
        self.move_up_callback = move_up_callback
        self.move_down_callback = move_down_callback
        self.settings_callback = settings_callback
        self.select_callback = select_callback
        
        # Settings state
        self.page_range = ""
        self.password = ""
        self.page_count = 0
        
        # Initialize UI
        self.is_dragging = False
        self.drag_start_y = 0
        self.thumbnail_label = None
        
        self.setup_ui()
        self.bind_drag_events()
        self.load_thumbnail()
        self.load_pdf_info()
        self.update_move_buttons()
    
    def setup_ui(self):
        """Setup the UI for this file frame"""
        self.grid_columnconfigure(1, weight=1)
        
        # Thumbnail placeholder
        self.thumbnail_placeholder = ctk.CTkFrame(
            self, 
            width=80, 
            height=104,
            fg_color=("gray90", "gray20"),
            corner_radius=4
        )
        self.thumbnail_placeholder.grid(row=0, column=0, rowspan=2, padx=(10, 5), pady=5, sticky="ns")
        
        self.loading_label = ctk.CTkLabel(
            self.thumbnail_placeholder,
            text="Loading...",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # File info frame
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        # File name with page range info
        self.file_name = os.path.basename(self.file_path)
        self.name_label = ctk.CTkLabel(
            self.info_frame,
            text=self.file_name,
            anchor="w",
            font=ctk.CTkFont(weight="bold"),
            cursor="hand2"
        )
        self.name_label.grid(row=0, column=0, padx=(0, 5), pady=(5, 0), sticky="w")
        
        # Page range indicator
        self.range_indicator = ctk.CTkLabel(
            self.info_frame,
            text="",
            text_color="blue",
            font=ctk.CTkFont(size=11),
            cursor="hand2"
        )
        self.range_indicator.grid(row=1, column=0, padx=(0, 5), pady=(0, 5), sticky="w")
        
        # File details (hidden when page range is set)
        self.details_label = ctk.CTkLabel(
            self.info_frame,
            text="",
            anchor="w",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.details_label.grid(row=2, column=0, padx=(0, 5), pady=(0, 5), sticky="w")
        
        # Bind clicks
        if self.select_callback:
            self.name_label.bind("<Button-1>", lambda e: self.select_callback(self.index))
            self.range_indicator.bind("<Button-1>", lambda e: self.select_callback(self.index))
        
        # Control buttons frame
        self.control_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.control_frame.grid(row=0, column=1, rowspan=3, padx=5, pady=5, sticky="e")
        
        # Move up button
        self.move_up_btn = ctk.CTkButton(
            self.control_frame,
            text="▲",
            width=28,
            height=28,
            command=lambda: self.move_up_callback(self.index) if self.move_up_callback else None,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            corner_radius=6
        )
        self.move_up_btn.grid(row=0, column=0, padx=2, pady=2)
        
        # Move down button
        self.move_down_btn = ctk.CTkButton(
            self.control_frame,
            text="▼",
            width=28,
            height=28,
            command=lambda: self.move_down_callback(self.index) if self.move_down_callback else None,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            corner_radius=6
        )
        self.move_down_btn.grid(row=1, column=0, padx=2, pady=2)
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            self.control_frame,
            text="⚙",
            width=28,
            height=28,
            command=lambda: self.open_settings() if self.settings_callback else None,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            corner_radius=6
        )
        self.settings_btn.grid(row=0, column=1, rowspan=2, padx=2, pady=2)
        
        # Drag handle
        self.drag_handle = ctk.CTkLabel(
            self.control_frame,
            text="☰",
            text_color="gray",
            cursor="hand2",
            font=ctk.CTkFont(size=16)
        )
        self.drag_handle.grid(row=0, column=2, rowspan=2, padx=2, pady=2)
        
        # Remove button
        self.remove_btn = ctk.CTkButton(
            self.control_frame,
            text="✕",
            width=28,
            height=28,
            command=lambda: self.remove_callback(self.index),
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            corner_radius=6
        )
        self.remove_btn.grid(row=0, column=3, rowspan=2, padx=2, pady=2)
    
    def load_pdf_info(self):
        """Load PDF information (page count, encryption)"""
        try:
            import fitz
            doc = fitz.open(self.file_path)
            self.total_pages = len(doc)
            self.is_encrypted = doc.is_encrypted
            doc.close()
            
            # Update details label
            file_stat = os.stat(self.file_path)
            file_size = self.format_file_size(file_stat.st_size)
            mod_date = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d")
            
            details_text = f"📄 {self.total_pages} pages | 📦 {file_size} | 📅 {mod_date}"
            if self.is_encrypted:
                details_text += " | 🔒 Encrypted"
            
            self.details_label.configure(text=details_text)
            
        except Exception as e:
            self.total_pages = 0
            self.is_encrypted = False
            self.details_label.configure(text="Error reading PDF")
    
    def load_thumbnail(self):
        """Load thumbnail asynchronously"""
        def update_thumbnail(ctk_image):
            if ctk_image and self.thumbnail_placeholder.winfo_exists():
                self.loading_label.destroy()
                self.thumbnail_label = ctk.CTkLabel(
                    self.thumbnail_placeholder,
                    image=ctk_image,
                    text=""
                )
                self.thumbnail_label.place(relx=0.5, rely=0.5, anchor="center")
                
                if self.select_callback:
                    self.thumbnail_label.bind("<Button-1>", lambda e: self.select_callback(self.index))
        
        self.preview_manager.get_thumbnail(
            self.file_path,
            size=(80, 104),
            callback=update_thumbnail
        )
    
    def set_page_range(self, page_range, password=""):
        """Set page range and password for this file"""
        from ..utils.page_range import PageRangeParser
        
        self.page_range = page_range
        self.password = password
        
        if page_range and self.total_pages > 0:
            page_count = PageRangeParser.get_page_count(page_range, self.total_pages)
            self.page_count = page_count
            
            range_text = f"📑 Pages: {page_range}"
            if page_count < self.total_pages:
                range_text += f" ({page_count} of {self.total_pages} pages)"
            
            self.range_indicator.configure(text=range_text)
            
            # Show/hide details based on advanced mode
            self.details_label.grid_remove()
        else:
            self.page_count = self.total_pages
            self.range_indicator.configure(text="")
            self.details_label.grid()
        
        # Update settings button color if password is set
        if password:
            self.settings_btn.configure(text_color="green", text="🔐")
        elif self.is_encrypted:
            self.settings_btn.configure(text_color="orange", text="🔒")
        else:
            self.settings_btn.configure(text_color=("gray10", "gray90"), text="⚙")
    
    def update_move_buttons(self):
        """Update up/down button states based on position"""
        # Up button: disabled if first item
        self.move_up_btn.configure(state="normal" if self.index > 0 else "disabled")
        
        # Down button: disabled if last item
        self.move_down_btn.configure(state="normal" if self.index < self.total_files - 1 else "disabled")
    
    def open_settings(self):
        """Open settings dialog for this file"""
        if self.settings_callback:
            self.settings_callback(self.index)
    
    def format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def bind_drag_events(self):
        """Bind drag and drop events"""
        self.drag_handle.bind("<ButtonPress-1>", self.on_drag_start)
        self.drag_handle.bind("<B1-Motion>", self.on_drag_motion)
        self.drag_handle.bind("<ButtonRelease-1>", self.on_drag_release)
        
        self.drag_handle.bind("<Enter>", lambda e: self.drag_handle.configure(text_color=("gray30", "gray70")))
        self.drag_handle.bind("<Leave>", lambda e: self.drag_handle.configure(text_color="gray"))
    
    def on_drag_start(self, event):
        self.is_dragging = True
        self.drag_start_y = event.y_root
        self.configure(fg_color=("gray85", "gray25"))
        self.drag_start_callback(self.index)
    
    def on_drag_motion(self, event):
        if self.is_dragging:
            self.place(y=event.y_root - self.drag_start_y)
    
    def on_drag_release(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.place_forget()
            self.configure(fg_color=("gray95", "gray20"))
            self.drag_end_callback(self.index, event.y_root)

class DraggableFileList(ctk.CTkScrollableFrame):
    """A scrollable frame with draggable file items with thumbnails and move buttons"""
    
    def __init__(self, master, files, file_settings, preview_manager, remove_callback, 
                 reorder_callback, move_up_callback, move_down_callback,
                 settings_callback=None, select_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.files = files
        self.file_settings = file_settings  # Dict mapping file_index -> {range, password}
        self.preview_manager = preview_manager
        self.remove_callback = remove_callback
        self.reorder_callback = reorder_callback
        self.move_up_callback = move_up_callback
        self.move_down_callback = move_down_callback
        self.settings_callback = settings_callback
        self.select_callback = select_callback
        
        self.dragged_index = None
        self.file_frames = []
        
        self.setup_ui()
    
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.update_file_list()
    
    def update_file_list(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        self.file_frames = []
        
        for i, file_path in enumerate(self.files):
            # Get settings for this file
            settings = self.file_settings.get(i, {})
            page_range = settings.get('range', '')
            password = settings.get('password', '')
            
            file_frame = DraggableFileFrame(
                self,
                file_path=file_path,
                index=i,
                total_files=len(self.files),
                preview_manager=self.preview_manager,
                remove_callback=self.remove_callback,
                drag_start_callback=self.on_drag_start,
                drag_end_callback=self.on_drag_end,
                move_up_callback=self.move_up_callback,
                move_down_callback=self.move_down_callback,
                settings_callback=self.settings_callback,
                select_callback=self.select_callback
            )
            
            # Apply settings
            file_frame.set_page_range(page_range, password)
            
            file_frame.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            self.file_frames.append(file_frame)
    
    def update_file_settings(self, index, page_range, password):
        """Update settings for a specific file"""
        if 0 <= index < len(self.file_frames):
            self.file_frames[index].set_page_range(page_range, password)
    
    def update_move_buttons(self):
        """Update all move buttons"""
        for i, file_frame in enumerate(self.file_frames):
            file_frame.index = i
            file_frame.total_files = len(self.files)
            file_frame.update_move_buttons()
    
    def on_drag_start(self, index):
        self.dragged_index = index
    
    def on_drag_end(self, index, drop_y):
        if self.dragged_index is not None:
            drop_index = self.calculate_drop_index(drop_y)
            if drop_index != self.dragged_index and drop_index is not None:
                self.reorder_callback(self.dragged_index, drop_index)
            self.dragged_index = None
    
    def calculate_drop_index(self, y_pos):
        widget_y = self.winfo_rooty()
        relative_y = y_pos - widget_y
        row_height = 120
        row_index = int(relative_y / row_height)
        return max(0, min(row_index, len(self.files) - 1))
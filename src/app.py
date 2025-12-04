import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from datetime import datetime

from .pdf_processor import PDFProcessor
from .utils.config_manager import ConfigManager
from .preview_manager import PreviewManager
from .ui_components.draggable_list import DraggableFileList
from .ui_components.preview_pane import PreviewPane
from .ui_components.file_settings_dialog import FileSettingsDialog

class PDFMergerApp(ctk.CTk):
    """Main application window for PDF Merger with all advanced features"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration
        self.config = ConfigManager()
        
        # Setup window - Fixed size
        self.title("PDF Merger")
        
        # Fixed window size (not resizable)
        width = 1200
        height = 700
        
        # Center window on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)  # Make window non-resizable
        
        # Apply saved theme and mode
        self.current_theme = self.config.get("theme", "system")
        self.advanced_mode = self.config.get("advanced_mode", False)
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")
        
        # Initialize managers
        self.preview_manager = PreviewManager()
        self.pdf_processor = PDFProcessor()
        
        # Store selected files and settings
        self.selected_files = []
        self.file_settings = {}  # {index: {'range': str, 'password': str}}
        self.selected_file_index = None
        
        # Setup UI with fixed panels
        self.setup_ui()
        
        # Bind window events
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Setup the main user interface with fixed layout"""
        # Configure grid layout with fixed proportions
        self.grid_columnconfigure(0, weight=3, minsize=700)  # Left panel minimum width
        self.grid_columnconfigure(1, weight=2, minsize=400)  # Right panel minimum width
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel - File management (FIXED WIDTH)
        self.left_panel = ctk.CTkFrame(self)
        self.left_panel.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.left_panel.grid_propagate(False)  # Prevent panel from resizing
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        # Set fixed row weights for left panel
        self.left_panel.grid_rowconfigure(0, weight=0)  # Top bar (fixed)
        self.left_panel.grid_rowconfigure(1, weight=0)  # Controls (fixed)
        self.left_panel.grid_rowconfigure(2, weight=1)  # File list (expandable)
        self.left_panel.grid_rowconfigure(3, weight=0)  # Bottom (fixed)
        
        # Right panel - Preview (FIXED WIDTH)
        self.right_panel = ctk.CTkFrame(self)
        self.right_panel.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.right_panel.grid_propagate(False)  # Prevent panel from resizing
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1)
        
        # Setup left panel components
        self.setup_left_panel()
        
        # Setup preview panel
        self.setup_preview_panel()
        
        # Set fixed panel sizes using .configure() instead of .config()
        self.update_idletasks()
        self.left_panel.configure(width=700, height=680)
        self.right_panel.configure(width=400, height=680)
    
    def setup_left_panel(self):
        """Setup the left panel with file controls"""
        # Top bar with title, theme, and mode toggle - STAYS AT TOP
        self.top_bar = ctk.CTkFrame(self.left_panel, height=50, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="ew")
        self.top_bar.grid_columnconfigure(0, weight=1)
        
        # Title with mode indicator
        mode_indicator = "🔧" if self.advanced_mode else "⚡"
        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text=f"{mode_indicator} PDF Merger",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Control buttons on right - STAYS AT TOP
        control_right = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        control_right.grid(row=0, column=1, padx=20, pady=10, sticky="e")
        
        # Advanced mode toggle
        self.mode_btn = ctk.CTkButton(
            control_right,
            text="Advanced Mode" if self.advanced_mode else "Simple Mode",
            command=self.toggle_mode,
            width=120,
            height=30,
            fg_color=("gray70", "gray30") if self.advanced_mode else ("gray85", "gray25")
        )
        self.mode_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Theme switcher
        self.theme_var = ctk.StringVar(value=self.current_theme)
        self.theme_menu = ctk.CTkOptionMenu(
            control_right,
            values=["light", "dark", "system"],
            variable=self.theme_var,
            command=self.change_theme,
            width=100,
            height=30
        )
        self.theme_menu.grid(row=0, column=1)
        
        # Control buttons frame - BELOW TOP BAR, ALSO STAYS AT TOP
        self.control_frame = ctk.CTkFrame(self.left_panel)
        self.control_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        self.add_files_btn = ctk.CTkButton(
            self.control_frame,
            text="📁 Add Files",
            command=self.add_files,
            width=100,
            height=35,
            corner_radius=8
        )
        self.add_files_btn.grid(row=0, column=0, padx=5, pady=10)
        
        self.add_folder_btn = ctk.CTkButton(
            self.control_frame,
            text="📂 Add Folder",
            command=self.add_folder,
            width=100,
            height=35,
            corner_radius=8
        )
        self.add_folder_btn.grid(row=0, column=1, padx=5, pady=10)
        
        self.sort_var = ctk.StringVar(value=self.config.get("sort_method", "alphabetical"))
        self.sort_menu = ctk.CTkOptionMenu(
            self.control_frame,
            values=["alphabetical", "date", "size", "custom"],
            variable=self.sort_var,
            command=self.apply_sort,
            width=100,
            height=35
        )
        self.sort_menu.grid(row=0, column=2, padx=5, pady=10)
        
        self.clear_btn = ctk.CTkButton(
            self.control_frame,
            text="🗑️ Clear All",
            command=self.clear_list,
            width=100,
            height=35,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "#DCE4EE"),
            corner_radius=8,
            hover_color=("gray70", "gray30")
        )
        self.clear_btn.grid(row=0, column=3, padx=5, pady=10)
        
        # File list container - EXPANDABLE AREA
        self.list_container = ctk.CTkFrame(self.left_panel)
        self.list_container.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.list_container.grid_columnconfigure(0, weight=1)
        self.list_container.grid_rowconfigure(0, weight=1)
        
        # Initialize draggable file list with up/down buttons
        list_label = "Drag ☰ or use ▲▼ to reorder | Click ⚙ for settings" if self.advanced_mode else "Drag ☰ or use ▲▼ to reorder | Click to preview"
        
        self.file_list = DraggableFileList(
            self.list_container,
            files=self.selected_files,
            file_settings=self.file_settings,
            preview_manager=self.preview_manager,
            remove_callback=self.remove_file,
            reorder_callback=self.reorder_files,
            move_up_callback=self.move_file_up,
            move_down_callback=self.move_file_down,
            settings_callback=self.open_file_settings if self.advanced_mode else None,
            select_callback=self.select_file_for_preview,
            label_text=list_label,
            label_font=ctk.CTkFont(weight="bold")
        )
        self.file_list.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Bottom controls - STAYS AT BOTTOM
        self.bottom_frame = ctk.CTkFrame(self.left_panel)
        self.bottom_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        
        # File count with page count in advanced mode
        self.file_count_label = ctk.CTkLabel(
            self.bottom_frame,
            text="No files selected",
            text_color="gray"
        )
        self.file_count_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Merge button
        merge_text = "🔗 Merge PDFs"
        if self.advanced_mode:
            total_pages = self.calculate_total_pages()
            merge_text = f"🔗 Merge ({total_pages} pages)"
        
        self.merge_btn = ctk.CTkButton(
            self.bottom_frame,
            text=merge_text,
            command=self.merge_files,
            width=120,
            height=40,
            font=ctk.CTkFont(weight="bold"),
            corner_radius=8
        )
        self.merge_btn.grid(row=0, column=1, padx=10, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.bottom_frame,
            text="Ready",
            text_color="gray"
        )
        self.status_label.grid(row=0, column=2, padx=20, pady=10, sticky="e")
        
        # Set initial state
        self.update_ui_state()
    
    def setup_preview_panel(self):
        """Setup the right preview panel"""
        self.preview_pane = PreviewPane(
            self.right_panel,
            preview_manager=self.preview_manager
        )
        self.preview_pane.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    def move_file_up(self, index):
        """Move a file up in the list"""
        if index > 0:
            self.reorder_files(index, index - 1)
    
    def move_file_down(self, index):
        """Move a file down in the list"""
        if index < len(self.selected_files) - 1:
            self.reorder_files(index, index + 1)
    
    def toggle_mode(self):
        """Toggle between simple and advanced mode"""
        self.advanced_mode = not self.advanced_mode
        self.config.set("advanced_mode", self.advanced_mode)
        
        # Update UI based on mode
        mode_indicator = "🔧" if self.advanced_mode else "⚡"
        self.title_label.configure(text=f"{mode_indicator} PDF Merger")
        self.mode_btn.configure(
            text="Advanced Mode" if self.advanced_mode else "Simple Mode",
            fg_color=("gray70", "gray30") if self.advanced_mode else ("gray85", "gray25")
        )
        
        # Update file list with/without settings buttons
        list_label = "Drag ☰ or use ▲▼ to reorder | Click ⚙ for settings" if self.advanced_mode else "Drag ☰ or use ▲▼ to reorder | Click to preview"
        self.file_list.settings_callback = self.open_file_settings if self.advanced_mode else None
        self.file_list.configure(label_text=list_label)
        
        # Update merge button text
        if self.advanced_mode and self.selected_files:
            total_pages = self.calculate_total_pages()
            self.merge_btn.configure(text=f"🔗 Merge ({total_pages} pages)")
        else:
            file_count = len(self.selected_files)
            self.merge_btn.configure(text=f"🔗 Merge {file_count} PDF{'s' if file_count != 1 else ''}")
        
        # Refresh file list to show/hide settings
        self.file_list.update_file_list()
        self.file_list.update_move_buttons()
    
    def calculate_total_pages(self):
        """Calculate total pages including page ranges"""
        total = 0
        for i, file_path in enumerate(self.selected_files):
            settings = self.file_settings.get(i, {})
            page_range = settings.get('range', '')
            
            if page_range:
                # Parse page range to count pages
                from .utils.page_range import PageRangeParser
                try:
                    import fitz
                    doc = fitz.open(file_path)
                    page_count = PageRangeParser.get_page_count(page_range, len(doc))
                    doc.close()
                    total += page_count
                except:
                    total += 1  # Fallback
            else:
                # Count all pages
                try:
                    import fitz
                    doc = fitz.open(file_path)
                    total += len(doc)
                    doc.close()
                except:
                    total += 1  # Fallback
        
        return total
    
    def select_file_for_preview(self, index):
        if 0 <= index < len(self.selected_files):
            self.selected_file_index = index
            pdf_path = self.selected_files[index]
            self.preview_pane.show_pdf_preview(pdf_path)
    
    def open_file_settings(self, index):
        """Open settings dialog for a file"""
        if 0 <= index < len(self.selected_files):
            file_path = self.selected_files[index]
            settings = self.file_settings.get(index, {})
            
            dialog = FileSettingsDialog(
                self,
                file_path=file_path,
                current_range=settings.get('range', ''),
                current_password=settings.get('password', '')
            )
            
            self.wait_window(dialog)
            
            if not dialog.cancelled:
                # Save settings
                self.file_settings[index] = {
                    'range': dialog.result_range,
                    'password': dialog.result_password
                }
                
                # Update file list display
                self.file_list.update_file_settings(index, dialog.result_range, dialog.result_password)
                
                # Update merge button with page count
                if self.advanced_mode:
                    total_pages = self.calculate_total_pages()
                    self.merge_btn.configure(text=f"🔗 Merge ({total_pages} pages)")
                
                self.update_status("Settings updated")
    
    def change_theme(self, new_theme):
        ctk.set_appearance_mode(new_theme)
        self.current_theme = new_theme
        self.config.set("theme", new_theme)
    
    def add_files(self):
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        initial_dir = self.config.get("last_directory", ".")
        
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=filetypes,
            initialdir=initial_dir
        )
        
        if files:
            self.config.set("last_directory", os.path.dirname(files[0]))
            added_count = 0
            
            for file_path in files:
                if file_path not in self.selected_files:
                    # Add file with default settings
                    self.selected_files.append(file_path)
                    added_count += 1
            
            if added_count > 0:
                self.update_file_list()
                self.update_status(f"Added {added_count} file(s)")
                self.apply_sort(self.sort_var.get())
    
    def add_folder(self):
        initial_dir = self.config.get("last_directory", ".")
        folder = filedialog.askdirectory(
            title="Select Folder with PDF Files",
            initialdir=initial_dir
        )
        
        if folder:
            self.config.set("last_directory", folder)
            pdf_files = []
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
            
            if pdf_files:
                added_count = 0
                for file_path in pdf_files:
                    if file_path not in self.selected_files:
                        self.selected_files.append(file_path)
                        added_count += 1
                
                if added_count > 0:
                    self.update_file_list()
                    self.update_status(f"Added {added_count} file(s) from folder")
                    self.apply_sort(self.sort_var.get())
                else:
                    messagebox.showinfo("No New Files", "All PDF files from this folder are already in the list.")
            else:
                messagebox.showwarning("No PDFs Found", "No PDF files found in the selected folder.")
    
    def clear_list(self):
        if self.selected_files:
            if messagebox.askyesno("Clear List", "Are you sure you want to clear all files?"):
                self.selected_files.clear()
                self.file_settings.clear()
                self.selected_file_index = None
                self.preview_pane.clear_preview()
                self.update_file_list()
                self.update_status("File list cleared")
    
    def apply_sort(self, sort_method):
        if not self.selected_files:
            return
        
        self.config.set("sort_method", sort_method)
        
        if sort_method == "custom":
            self.update_status("Custom order (drag to reorder)")
            return
        
        # Store current settings with file paths
        old_settings = {}
        for i, file_path in enumerate(self.selected_files):
            if i in self.file_settings:
                old_settings[file_path] = self.file_settings[i]
        
        # Sort files
        if sort_method == "alphabetical":
            self.selected_files.sort(key=lambda x: os.path.basename(x).lower())
        elif sort_method == "date":
            self.selected_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        elif sort_method == "size":
            self.selected_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
        
        # Reapply settings to new positions
        new_settings = {}
        for i, file_path in enumerate(self.selected_files):
            if file_path in old_settings:
                new_settings[i] = old_settings[file_path]
        
        self.file_settings = new_settings
        
        # Update selected file index
        if self.selected_file_index is not None:
            try:
                # Find the new index of the previously selected file
                old_path = self.selected_files[self.selected_file_index]
                new_index = self.selected_files.index(old_path)
                self.selected_file_index = new_index
            except:
                self.selected_file_index = None
        
        self.update_file_list()
        self.update_status(f"Sorted by {sort_method}")
    
    def update_file_list(self):
        self.file_list.files = self.selected_files
        self.file_list.file_settings = self.file_settings
        self.file_list.update_file_list()
        self.file_list.update_move_buttons()
        self.update_ui_state()
    
    def remove_file(self, index):
        if 0 <= index < len(self.selected_files):
            removed_file = self.selected_files.pop(index)
            
            # Remove settings for this file
            if index in self.file_settings:
                del self.file_settings[index]
            
            # Shift settings for files after this one
            new_settings = {}
            for i, file_path in enumerate(self.selected_files):
                old_index = self.selected_files.index(file_path)
                if old_index + 1 in self.file_settings:
                    new_settings[i] = self.file_settings[old_index + 1]
            
            self.file_settings = new_settings
            
            # Update selected file index
            if self.selected_file_index == index:
                self.selected_file_index = None
                self.preview_pane.clear_preview()
            elif self.selected_file_index and self.selected_file_index > index:
                self.selected_file_index -= 1
            
            self.update_file_list()
            self.update_status(f"Removed: {os.path.basename(removed_file)}")
    
    def reorder_files(self, from_index, to_index):
        if 0 <= from_index < len(self.selected_files) and 0 <= to_index < len(self.selected_files):
            # Move file
            item = self.selected_files.pop(from_index)
            self.selected_files.insert(to_index, item)
            
            # Move settings
            if from_index in self.file_settings:
                settings = self.file_settings[from_index]
                del self.file_settings[from_index]
                
                # Adjust other settings
                new_settings = {}
                for i, file_path in enumerate(self.selected_files):
                    old_index = i
                    if i > from_index and i <= to_index:
                        old_index -= 1
                    elif i < from_index and i >= to_index:
                        old_index += 1
                    
                    if old_index in self.file_settings:
                        new_settings[i] = self.file_settings[old_index]
                
                # Insert moved settings
                new_settings[to_index] = settings
                self.file_settings = new_settings
            
            # Update selected file index
            if self.selected_file_index == from_index:
                self.selected_file_index = to_index
            elif self.selected_file_index:
                if from_index < self.selected_file_index <= to_index:
                    self.selected_file_index -= 1
                elif to_index <= self.selected_file_index < from_index:
                    self.selected_file_index += 1
            
            self.update_file_list()
            self.update_status("Files reordered")
            self.sort_var.set("custom")
    
    def merge_files(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select PDF files to merge.")
            return
        
        if len(self.selected_files) == 1:
            if not messagebox.askyesno("Single File", "Only one file selected. Merge anyway?"):
                return
        
        # Check for password errors in advanced mode
        if self.advanced_mode:
            for i, file_path in enumerate(self.selected_files):
                if i in self.file_settings:
                    password = self.file_settings[i].get('password', '')
                    if password:
                        # Test password
                        success, message = self.pdf_processor.validate_pdf(file_path, password)
                        if not success:
                            retry = messagebox.askyesno(
                                "Password Error",
                                f"File: {os.path.basename(file_path)}\nError: {message}\n\nDo you want to fix the settings?"
                            )
                            if retry:
                                self.open_file_settings(i)
                                return
        
        initial_dir = self.config.get("last_directory", ".")
        default_name = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        output_file = filedialog.asksaveasfilename(
            title="Save Merged PDF As",
            defaultextension=".pdf",
            initialfile=default_name,
            initialdir=initial_dir,
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if not output_file:
            return
        
        self.config.set("last_directory", os.path.dirname(output_file))
        
        # Show progress
        self.progress_window = ctk.CTkToplevel(self)
        self.progress_window.title("Merging PDFs")
        self.progress_window.geometry("400x200")
        self.progress_window.transient(self)
        self.progress_window.grab_set()
        
        # Center on main window
        self.progress_window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - self.progress_window.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - self.progress_window.winfo_height()) // 2
        self.progress_window.geometry(f"+{x}+{y}")
        
        progress_label = ctk.CTkLabel(
            self.progress_window,
            text=f"Merging {len(self.selected_files)} files...",
            font=ctk.CTkFont(size=14)
        )
        progress_label.pack(pady=(30, 10))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_window, width=300)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Status label in progress window
        self.progress_status = ctk.CTkLabel(
            self.progress_window,
            text="Starting...",
            text_color="gray"
        )
        self.progress_status.pack(pady=10)
        
        self.after(100, lambda: self.perform_merge(output_file))
    
    def perform_merge(self, output_file):
        try:
            # Perform merge with settings
            success, message = self.pdf_processor.merge_pdfs(
                self.selected_files,
                output_file,
                self.file_settings if self.advanced_mode else {}
            )
            
            self.progress_window.destroy()
            
            if success:
                self.update_status("Merge completed successfully!")
                
                result = messagebox.askyesnocancel(
                    "Success", 
                    f"✅ PDFs merged successfully!\n\nSaved to:\n{output_file}\n\nWhat would you like to do?",
                    detail="Click 'Yes' to open the file, 'No' to open the folder, or 'Cancel' to do nothing."
                )
                
                if result is True:
                    os.startfile(output_file) if os.name == 'nt' else os.system(f'open "{output_file}"')
                elif result is False:
                    folder_path = os.path.dirname(output_file)
                    os.startfile(folder_path) if os.name == 'nt' else os.system(f'open "{folder_path}"')
                    
            else:
                self.update_status("Merge failed")
                messagebox.showerror("Merge Failed", f"❌ Error: {message}")
                
        except Exception as e:
            if hasattr(self, 'progress_window') and self.progress_window:
                self.progress_window.destroy()
            
            self.update_status("Merge failed")
            messagebox.showerror("Error", f"❌ An unexpected error occurred:\n{str(e)}")
    
    def update_ui_state(self):
        has_files = len(self.selected_files) > 0
        
        if has_files:
            total_size = sum(os.path.getsize(f) for f in self.selected_files if os.path.exists(f))
            size_text = self.format_file_size(total_size)
            
            if self.advanced_mode:
                total_pages = self.calculate_total_pages()
                page_text = f" | 📄 {total_pages} pages"
            else:
                page_text = ""
            
            self.file_count_label.configure(
                text=f"{len(self.selected_files)} files ({size_text}{page_text})",
                text_color=("gray10", "gray90")
            )
        else:
            self.file_count_label.configure(
                text="No files selected",
                text_color="gray"
            )
        
        self.clear_btn.configure(state="normal" if has_files else "disabled")
        self.merge_btn.configure(state="normal" if has_files else "disabled")
        self.sort_menu.configure(state="normal" if has_files else "disabled")
        
        if has_files:
            if self.advanced_mode:
                total_pages = self.calculate_total_pages()
                self.merge_btn.configure(text=f"🔗 Merge ({total_pages} pages)")
            else:
                self.merge_btn.configure(text=f"🔗 Merge {len(self.selected_files)} PDF{'s' if len(self.selected_files) != 1 else ''}")
    
    def format_file_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def update_status(self, message):
        self.status_label.configure(text=message)
        self.update_idletasks()
    
    def on_closing(self):
        """Handle application closing"""
        # Clean up preview manager
        self.preview_manager.cleanup()
        
        # Save configuration
        self.config.save()
        self.destroy()

if __name__ == "__main__":
    app = PDFMergerApp()
    app.mainloop()
import customtkinter as ctk
from tkinter import messagebox
import fitz  # PyMuPDF
from ..utils.page_range import PageRangeParser

class FileSettingsDialog(ctk.CTkToplevel):
    """Dialog for configuring page range and password for a PDF file"""
    
    def __init__(self, parent, file_path, current_range="", current_password="", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.file_path = file_path
        self.result_range = current_range
        self.result_password = current_password
        self.cancelled = True
        
        # Get PDF info
        self.total_pages = 0
        self.is_encrypted = False
        
        try:
            doc = fitz.open(file_path)
            self.total_pages = len(doc)
            self.is_encrypted = doc.is_encrypted
            doc.close()
        except:
            pass
        
        self.setup_ui()
        self.center_on_parent()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.title("PDF Settings")
        self.geometry("500x350")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(self.master)
        self.grab_set()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # File info
        file_name = self.file_path.split('/')[-1]
        info_text = f"File: {file_name}"
        if self.total_pages > 0:
            info_text += f" ({self.total_pages} pages)"
        
        info_label = ctk.CTkLabel(
            self,
            text=info_text,
            font=ctk.CTkFont(weight="bold"),
            wraplength=450
        )
        info_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Page range section
        range_frame = ctk.CTkFrame(self)
        range_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        range_frame.grid_columnconfigure(1, weight=1)
        
        range_label = ctk.CTkLabel(
            range_frame,
            text="Page Range:",
            font=ctk.CTkFont(weight="bold")
        )
        range_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.range_var = ctk.StringVar(value=self.result_range or "")
        self.range_entry = ctk.CTkEntry(
            range_frame,
            textvariable=self.range_var,
            placeholder_text="e.g., 1,3,5-8 or leave blank for all pages",
            width=300
        )
        self.range_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Range help text
        help_text = "Examples: '1,3,5' (pages 1,3,5) | '1-5' (pages 1 to 5) | '1,3-5,7' (mixed)"
        help_label = ctk.CTkLabel(
            range_frame,
            text=help_text,
            text_color="gray",
            font=ctk.CTkFont(size=12),
            wraplength=400
        )
        help_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
        
        # Page count preview
        self.page_count_label = ctk.CTkLabel(
            range_frame,
            text=f"Will include: {self.total_pages} pages",
            text_color="gray"
        )
        self.page_count_label.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
        
        # Bind range validation
        self.range_var.trace_add("write", self.validate_range)
        
        # Password section (only show if encrypted or password provided)
        if self.is_encrypted or self.result_password:
            password_frame = ctk.CTkFrame(self)
            password_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
            password_frame.grid_columnconfigure(1, weight=1)
            
            password_label = ctk.CTkLabel(
                password_frame,
                text="Password:",
                font=ctk.CTkFont(weight="bold")
            )
            password_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            
            self.password_var = ctk.StringVar(value=self.result_password or "")
            self.password_entry = ctk.CTkEntry(
                password_frame,
                textvariable=self.password_var,
                placeholder_text="Enter password for encrypted PDF",
                show="•",
                width=300
            )
            self.password_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            
            # Encryption status
            status_text = "🔒 Encrypted PDF" if self.is_encrypted else "Password saved"
            status_label = ctk.CTkLabel(
                password_frame,
                text=status_text,
                text_color="orange" if self.is_encrypted else "green",
                font=ctk.CTkFont(size=12)
            )
            status_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
        
        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=100,
            fg_color="transparent",
            border_width=1
        )
        cancel_btn.grid(row=0, column=0, padx=10, sticky="e")
        
        # Save button
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Save Settings",
            command=self.save,
            width=100
        )
        self.save_btn.grid(row=0, column=1, padx=10, sticky="w")
        
        # Initial validation
        self.validate_range()
    
    def validate_range(self, *args):
        """Validate page range input"""
        range_str = self.range_var.get()
        
        if not range_str.strip():
            # Empty means all pages
            page_count = self.total_pages
            self.page_count_label.configure(
                text=f"Will include: {page_count} pages (all)",
                text_color="gray"
            )
            self.save_btn.configure(state="normal")
            return True
        
        success, page_numbers, error = PageRangeParser.parse_range(range_str, self.total_pages)
        
        if success:
            page_count = len(page_numbers)
            self.page_count_label.configure(
                text=f"Will include: {page_count} of {self.total_pages} pages",
                text_color="green"
            )
            self.save_btn.configure(state="normal")
            return True
        else:
            self.page_count_label.configure(
                text=f"Error: {error}",
                text_color="red"
            )
            self.save_btn.configure(state="disabled")
            return False
    
    def center_on_parent(self):
        """Center dialog on parent window"""
        self.update_idletasks()
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def save(self):
        """Save settings and close dialog"""
        if not self.validate_range():
            messagebox.showerror("Invalid Range", "Please fix the page range error.")
            return
        
        self.result_range = self.range_var.get().strip()
        
        if hasattr(self, 'password_var'):
            self.result_password = self.password_var.get()
        else:
            self.result_password = ""
        
        self.cancelled = False
        self.destroy()
    
    def cancel(self):
        """Cancel dialog"""
        self.cancelled = True
        self.destroy()
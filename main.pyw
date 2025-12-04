import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import customtkinter as ctk
from src.app import PDFMergerApp

def main():
    """Main entry point for PDF Merger application"""
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    
    app = PDFMergerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
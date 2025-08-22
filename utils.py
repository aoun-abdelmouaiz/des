"""
Utility functions for the Vehicle Repair Workshop Management System
"""
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import subprocess
import platform
from datetime import datetime, timedelta
from typing import Optional, Any
import config
import shutil
import uuid
from pathlib import Path

def show_error(title: str, message: str):
    """Show error message dialog"""
    messagebox.showerror(title, message)

def show_info(title: str, message: str):
    """Show info message dialog"""
    messagebox.showinfo(title, message)

def show_warning(title: str, message: str):
    """Show warning message dialog"""
    messagebox.showwarning(title, message)

def ask_yes_no(title: str, message: str) -> bool:
    """Ask yes/no question dialog"""
    return messagebox.askyesno(title, message)

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove spaces and dashes
    phone_clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    # Check if it contains only digits and has reasonable length
    return phone_clean.isdigit() and 7 <= len(phone_clean) <= 15

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"

def format_date(date_str: str) -> str:
    """Format date string for display"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%m/%d/%Y')
    except:
        return date_str

def get_date_range_options() -> list:
    """Get predefined date range options"""
    today = datetime.now()
    options = [
        ("Today", today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
        ("This Week", (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
        ("This Month", today.replace(day=1).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
        ("Last Month", (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d'), 
         (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')),
        ("This Year", today.replace(month=1, day=1).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
        ("Last Year", today.replace(year=today.year-1, month=1, day=1).strftime('%Y-%m-%d'),
         today.replace(year=today.year-1, month=12, day=31).strftime('%Y-%m-%d'))
    ]
    return options

def load_image(image_path: str, size: tuple = None) -> Optional[ImageTk.PhotoImage]:
    """Load and resize image for tkinter"""
    try:
        if not os.path.exists(image_path):
            return None
        
        image = Image.open(image_path)
        if size:
            image = image.resize(size, Image.Resampling.LANCZOS)
        
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def select_image_file() -> Optional[str]:
    """Open file dialog to select an image"""
    filetypes = [
        ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
        ("PNG files", "*.png"),
        ("JPEG files", "*.jpg *.jpeg"),
        ("All files", "*.*")
    ]
    
    return filedialog.askopenfilename(
        title="Select Image",
        filetypes=filetypes,
        initialdir=config.LOGOS_DIR
    )

def select_attachment_file() -> Optional[str]:
    """Open file dialog to select an attachment (images, pdf, documents)."""
    filetypes = [
        ("Common", "*.png *.jpg *.jpeg *.gif *.bmp *.pdf *.doc *.docx *.xls *.xlsx *.txt"),
        ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
        ("PDF", "*.pdf"),
        ("Word", "*.doc *.docx"),
        ("Excel", "*.xls *.xlsx"),
        ("Text", "*.txt"),
        ("All files", "*.*"),
    ]
    return filedialog.askopenfilename(title="Select Attachment", filetypes=filetypes)

def save_attachment_for_item(src_path: str, work_order_id: int, item_type: str, item_id: Optional[int] = None) -> Optional[str]:
    """Copy the selected attachment into assets under work_orders/services or spare_parts.

    item_type: "service" or "part".
    Returns the relative saved path string, or None if failed.
    """
    try:
        if not src_path or not os.path.exists(src_path):
            return None
        # If already within assets, don't copy
        try:
            assets_root = (config.ASSETS_DIR).resolve()
            src_resolved = (Path(src_path)).resolve()
            src_resolved.relative_to(assets_root)
            return str(src_resolved)
        except Exception:
            pass
        # Determine base directory
        if item_type == "service":
            base_dir = config.ASSETS_SERVICE_ATTACHMENTS_DIR
        else:
            base_dir = config.ASSETS_PART_ATTACHMENTS_DIR
        # Create work order subfolder
        target_dir = base_dir / f"wo_{work_order_id}"
        target_dir.mkdir(parents=True, exist_ok=True)
        # Build unique filename, preserving extension
        ext = os.path.splitext(src_path)[1]
        unique = uuid.uuid4().hex[:12]
        name = f"{item_type}_{item_id or 'new'}_{unique}{ext}"
        dst_path = target_dir / name
        shutil.copy2(src_path, dst_path)
        return str(dst_path)
    except Exception as e:
        show_error("Error", f"Failed to save attachment: {e}")
        return None

def open_if_exists(file_path: Optional[str]):
    """Open a file if the path exists."""
    if not file_path:
        show_warning("No Attachment", "No attachment available for this item.")
        return
    if not os.path.exists(file_path):
        show_error("Missing File", "The attachment file was not found on disk.")
        return
    open_file_externally(file_path)

def save_file_dialog(defaultextension: str = ".pdf", filetypes: list = None) -> Optional[str]:
    """Open save file dialog"""
    if filetypes is None:
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
    
    return filedialog.asksaveasfilename(
        defaultextension=defaultextension,
        filetypes=filetypes,
        initialdir=config.EXPORTS_DIR
    )

def open_file_externally(filepath: str):
    """Open file with system default application"""
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':  # Windows
            os.startfile(filepath)
        else:  # Linux
            subprocess.call(('xdg-open', filepath))
    except Exception as e:
        show_error("Error", f"Could not open file: {e}")

def center_window(window: tk.Tk, width: int, height: int):
    """Center window on screen"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    window.geometry(f"{width}x{height}+{x}+{y}")

def create_tooltip(widget, text: str):
    """Create tooltip for widget"""
    def on_enter(event):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = tk.Label(tooltip, text=text, background="lightyellow", 
                        relief="solid", borderwidth=1, font=config.FONTS['small'])
        label.pack()
        
        widget.tooltip = tooltip
    
    def on_leave(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def validate_float(value: str) -> bool:
    """Validate if string can be converted to float"""
    try:
        float(value)
        return True
    except ValueError:
        return False

def validate_int(value: str) -> bool:
    """Validate if string can be converted to integer"""
    try:
        int(value)
        return True
    except ValueError:
        return False

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text with ellipsis if too long"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

class NumberEntry(tk.Entry):
    """Entry widget that only allows numbers"""
    def __init__(self, parent, allow_decimal=True, **kwargs):
        super().__init__(parent, **kwargs)
        self.allow_decimal = allow_decimal
        
        vcmd = (self.register(self.validate_input), '%P')
        self.config(validate='key', validatecommand=vcmd)
    
    def validate_input(self, value_if_allowed):
        if value_if_allowed == "":
            return True
        
        if self.allow_decimal:
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return value_if_allowed.isdigit()

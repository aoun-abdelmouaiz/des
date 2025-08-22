"""
Dialog windows for the Vehicle Repair Workshop Management System
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from datetime import datetime
import config
import utils
from models import Customer, Vehicle, WorkOrder, Service, SparePart

class BaseDialog:
    """Base class for all dialog windows"""
    def __init__(self, parent, title, size=(400, 300)):
        self.parent = parent
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        self.dialog.transient(parent)
        
        # Center the dialog
        utils.center_window(self.dialog, size[0], size[1])
        
        self.create_widgets()
        
    def create_widgets(self):
        """Override in subclasses"""
        pass
    
    def on_ok(self):
        """Override in subclasses"""
        self.dialog.destroy()
    
    def on_cancel(self):
        """Cancel dialog"""
        self.result = None
        self.dialog.destroy()

class CustomerDialog(BaseDialog):
    """Dialog for adding/editing customers"""
    def __init__(self, parent, customer=None):
        self.customer = customer
        self.is_edit = customer is not None
        title = "Edit Customer" if self.is_edit else "Add Customer"
        super().__init__(parent, title, (450, 300))
        
        if self.is_edit:
            self.load_customer_data()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Name field
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky=W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        self.name_entry.focus()
        
        # Phone field
        ttk.Label(main_frame, text="Phone:").grid(row=1, column=0, sticky=W, pady=5)
        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(main_frame, textvariable=self.phone_var, width=40)
        self.phone_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Address field
        ttk.Label(main_frame, text="Address:").grid(row=2, column=0, sticky=NW, pady=5)
        self.address_var = tk.StringVar()
        self.address_entry = tk.Text(main_frame, width=30, height=4)
        self.address_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self.on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
    
    def load_customer_data(self):
        """Load customer data for editing"""
        self.name_var.set(self.customer.get('name', ''))
        self.phone_var.set(self.customer.get('phone', ''))
        address = self.customer.get('address', '')
        self.address_entry.insert('1.0', address)
    
    def on_ok(self):
        # Validate input
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        address = self.address_entry.get('1.0', tk.END).strip()
        
        if not name:
            utils.show_error("Validation Error", "Name is required")
            return
        
        if not phone:
            utils.show_error("Validation Error", "Phone is required")
            return
        
        if not utils.validate_phone(phone):
            utils.show_error("Validation Error", "Please enter a valid phone number")
            return
        
        # No-changes detection in edit mode
        if self.is_edit:
            old_name = self.customer.get('name', '').strip()
            old_phone = self.customer.get('phone', '').strip()
            old_address = (self.customer.get('address') or '').strip()
            if name == old_name and phone == old_phone and address == old_address:
                utils.show_warning("No changes detected", "No changes detected")
                return
        
        self.result = {
            'name': name,
            'phone': phone,
            'address': address
        }
        
        self.dialog.destroy()

class VehicleDialog(BaseDialog):
    """Dialog for adding/editing vehicles"""
    def __init__(self, parent, db_manager, vehicle=None):
        self.db_manager = db_manager
        self.vehicle = vehicle
        self.is_edit = vehicle is not None
        title = "Edit Vehicle" if self.is_edit else "Add Vehicle"
        super().__init__(parent, title, (520, 340))
        
        if self.is_edit:
            self.load_vehicle_data()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        # License Plate field
        ttk.Label(main_frame, text="License Plate:").grid(row=0, column=0, sticky=W, pady=5)
        self.license_var = tk.StringVar()
        self.license_entry = ttk.Entry(main_frame, textvariable=self.license_var, width=40)
        self.license_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        self.license_entry.focus()
        
        # Brand field (readonly combobox)
        ttk.Label(main_frame, text="Brand:").grid(row=1, column=0, sticky=W, pady=5)
        self.brand_var = tk.StringVar()
        self.brand_combo = ttk.Combobox(main_frame, textvariable=self.brand_var, width=37, state='readonly')
        self.brand_combo.grid(row=1, column=1, pady=5, padx=(10, 0))
        self.brand_combo.bind('<<ComboboxSelected>>', self.on_brand_change)
        self.load_brands()
        
        # Model field (readonly combobox filtered by brand)
        ttk.Label(main_frame, text="Model:").grid(row=2, column=0, sticky=W, pady=5)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(main_frame, textvariable=self.model_var, width=37, state='readonly')
        self.model_combo.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Customer Phone field with autocomplete
        ttk.Label(main_frame, text="Customer Phone:").grid(row=3, column=0, sticky=W, pady=5)
        phone_frame = ttk.Frame(main_frame)
        phone_frame.grid(row=3, column=1, pady=5, padx=(10, 0), sticky=W+E)
        
        self.phone_var = tk.StringVar()
        self.phone_combo = ttk.Combobox(phone_frame, textvariable=self.phone_var, width=30)
        self.phone_combo.pack(side=LEFT)
        self.phone_combo.bind('<KeyRelease>', self.on_phone_type)
        self.phone_combo.bind('<<ComboboxSelected>>', self.on_phone_select)
        
        # Initial load of customers
        self.load_customer_phones("")
        
        ttk.Button(phone_frame, text="Refresh", command=lambda: self.load_customer_phones(""),
                  bootstyle=OUTLINE).pack(side=LEFT, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self.on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
    
    def load_brands(self):
        try:
            brands = self.db_manager.get_brands()
            self.brand_combo['values'] = brands
        except Exception:
            self.brand_combo['values'] = []
    
    def on_brand_change(self, event=None):
        brand = self.brand_var.get().strip()
        try:
            models = self.db_manager.get_models_by_brand(brand) if brand else []
            self.model_combo['values'] = models
            # Clear model selection if brand changed
            if self.model_var.get() not in models:
                self.model_var.set('')
        except Exception:
            self.model_combo['values'] = []
    
    def load_customer_phones(self, search_term: str):
        try:
            if search_term:
                customers = self.db_manager.search_customers(search_term)
            else:
                customers = self.db_manager.get_customers()
            phone_list = [f"{customer['phone']} - {customer['name']}" for customer in customers]
            self.phone_combo['values'] = phone_list
        except Exception:
            self.phone_combo['values'] = []
    
    def on_phone_type(self, event=None):
        term = self.phone_var.get().strip()
        self.load_customer_phones(term)
    
    def on_phone_select(self, event=None):
        # Keep selection as 'phone - name'; parsing will extract phone on save
        pass
    
    def load_vehicle_data(self):
        """Load vehicle data for editing"""
        self.license_var.set(self.vehicle.get('license_plate', ''))
        # For brand/model, populate combos then set values
        self.load_brands()
        brand_value = self.vehicle.get('brand', '')
        model_value = self.vehicle.get('model', '')
        if brand_value:
            self.brand_var.set(brand_value)
            try:
                self.model_combo['values'] = self.db_manager.get_models_by_brand(brand_value)
            except Exception:
                self.model_combo['values'] = []
        if model_value:
            self.model_var.set(model_value)
        
        # Set customer phone
        customer_phone = self.vehicle.get('customer_phone', '')
        customer_name = self.vehicle.get('customer_name', '')
        if customer_phone:
            self.phone_var.set(f"{customer_phone} - {customer_name}")
    
    def on_ok(self):
        # Validate input
        license_plate = self.license_var.get().strip()
        brand = self.brand_var.get().strip()
        model = self.model_var.get().strip()
        phone_selection = self.phone_var.get().strip()
        
        if not license_plate:
            utils.show_error("Validation Error", "License plate is required")
            return
        
        if not brand:
            utils.show_error("Validation Error", "Brand is required")
            return
        
        if not model:
            utils.show_error("Validation Error", "Model is required")
            return
        
        if not phone_selection:
            utils.show_error("Validation Error", "Customer must be selected")
            return
        
        # Extract phone number from selection (support plain phone too)
        if ' - ' in phone_selection:
            customer_phone = phone_selection.split(' - ')[0]
        else:
            customer_phone = phone_selection
        
        # No-changes detection in edit mode
        if self.is_edit:
            old_lp = (self.vehicle.get('license_plate') or '').strip()
            old_brand = (self.vehicle.get('brand') or '').strip()
            old_model = (self.vehicle.get('model') or '').strip()
            old_phone = (self.vehicle.get('customer_phone') or '').strip()
            if (license_plate == old_lp and brand == old_brand and model == old_model and customer_phone == old_phone):
                utils.show_warning("No changes detected", "No changes detected")
                return
        
        self.result = {
            'license_plate': license_plate,
            'brand': brand,
            'model': model,
            'customer_phone': customer_phone
        }
        
        self.dialog.destroy()

class WorkOrderDialog(BaseDialog):
    """Dialog for creating new work orders"""
    def __init__(self, parent, db_manager):
        self.db_manager = db_manager
        super().__init__(parent, "Create Work Order", (550, 250))
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Vehicle selection
        ttk.Label(main_frame, text="Vehicle:").grid(row=0, column=0, sticky=W, pady=5)
        
        vehicle_frame = ttk.Frame(main_frame)
        vehicle_frame.grid(row=0, column=1, pady=5, padx=(10, 0), sticky=W+E)
        
        self.vehicle_var = tk.StringVar()
        self.vehicle_combo = ttk.Combobox(vehicle_frame, textvariable=self.vehicle_var, width=40)
        self.vehicle_combo.pack(side=LEFT)
        
        # Load vehicles
        self.load_vehicles()
        
        ttk.Button(vehicle_frame, text="Refresh", command=self.load_vehicles,
                  bootstyle=OUTLINE).pack(side=LEFT, padx=(5, 0))
        
        # Entry date
        ttk.Label(main_frame, text="Entry Date:").grid(row=1, column=0, sticky=W, pady=5)
        self.date_var = tk.StringVar()
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
        self.date_entry = ttk.Entry(main_frame, textvariable=self.date_var, width=40)
        self.date_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Status
        ttk.Label(main_frame, text="Status:").grid(row=2, column=0, sticky=W, pady=5)
        self.status_var = tk.StringVar(value="Open")
        self.status_combo = ttk.Combobox(main_frame, textvariable=self.status_var, 
                                        values=["Open", "In Progress", "Completed"], width=37)
        self.status_combo.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Create", command=self.on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
    
    def load_vehicles(self):
        """Load vehicles for selection"""
        vehicles = self.db_manager.get_vehicles()
        vehicle_list = [f"{vehicle['license_plate']} - {vehicle['brand']} {vehicle['model']} ({vehicle['customer_name']})" 
                       for vehicle in vehicles]
        self.vehicle_combo['values'] = vehicle_list
    
    def on_ok(self):
        # Validate input
        vehicle_selection = self.vehicle_var.get().strip()
        entry_date = self.date_var.get().strip()
        status = self.status_var.get().strip()
        
        if not vehicle_selection:
            utils.show_error("Validation Error", "Vehicle must be selected")
            return
        
        if not entry_date:
            utils.show_error("Validation Error", "Entry date is required")
            return
        
        # Validate date format
        try:
            datetime.strptime(entry_date, '%Y-%m-%d')
        except ValueError:
            utils.show_error("Validation Error", "Date must be in YYYY-MM-DD format")
            return
        
        # Get vehicle ID from selection
        license_plate = vehicle_selection.split(' - ')[0]
        vehicles = self.db_manager.get_vehicles()
        vehicle_id = None
        for vehicle in vehicles:
            if vehicle['license_plate'] == license_plate:
                vehicle_id = vehicle['id']
                break
        
        if not vehicle_id:
            utils.show_error("Error", "Vehicle not found")
            return
        
        self.result = {
            'vehicle_id': vehicle_id,
            'entry_date': entry_date,
            'status': status
        }
        
        self.dialog.destroy()

class ServiceDialog(BaseDialog):
    """Dialog for adding services to work orders"""
    def __init__(self, parent, service=None):
        self.service = service
        self.is_edit = service is not None
        title = "Edit Service" if self.is_edit else "Add Service"
        super().__init__(parent, title, (510, 420))
        
        if self.is_edit:
            self.load_service_data()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Service name
        ttk.Label(main_frame, text="Service Name:").grid(row=0, column=0, sticky=W, pady=5)
        self.name_var = tk.StringVar()
        self.name_combo = ttk.Combobox(main_frame, textvariable=self.name_var, width=40)
        self.name_combo['values'] = config.DEFAULT_SERVICES
        self.name_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=1, column=0, sticky=NW, pady=5)
        self.description_entry = tk.Text(main_frame, width=30, height=4)
        self.description_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:").grid(row=2, column=0, sticky=W, pady=5)
        self.quantity_var = tk.StringVar(value="1")
        self.quantity_entry = utils.NumberEntry(main_frame, textvariable=self.quantity_var, 
                                               allow_decimal=False, width=40)
        self.quantity_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Price
        ttk.Label(main_frame, text="Unit Price ($):").grid(row=3, column=0, sticky=W, pady=5)
        self.price_var = tk.StringVar(value="0.00")
        self.price_entry = utils.NumberEntry(main_frame, textvariable=self.price_var, width=40)
        self.price_entry.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        # Total (calculated)
        ttk.Label(main_frame, text="Total:").grid(row=4, column=0, sticky=W, pady=5)
        self.total_label = ttk.Label(main_frame, text="$0.00", font=config.FONTS['header'])
        self.total_label.grid(row=4, column=1, sticky=W, pady=5, padx=(10, 0))
        
        # Attachment
        ttk.Label(main_frame, text="Attachment:").grid(row=5, column=0, sticky=W, pady=5)
        attach_frame = ttk.Frame(main_frame)
        attach_frame.grid(row=5, column=1, sticky=W, pady=5, padx=(10, 0))
        self.attachment_path = tk.StringVar()
        self.attachment_entry = ttk.Entry(attach_frame, textvariable=self.attachment_path, width=32)
        self.attachment_entry.pack(side=LEFT)
        ttk.Button(attach_frame, text="Browse", command=self.on_browse_attachment, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(attach_frame, text="Open", command=self.on_open_attachment, bootstyle=SECONDARY).pack(side=LEFT)
        
        # Bind events to update total
        self.quantity_var.trace('w', self.update_total)
        self.price_var.trace('w', self.update_total)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Add" if not self.is_edit else "Save", command=self.on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
    
    def load_service_data(self):
        """Load service data for editing"""
        self.name_var.set(self.service.get('name', ''))
        description = self.service.get('description', '')
        self.description_entry.insert('1.0', description)
        self.quantity_var.set(str(self.service.get('quantity', 1)))
        self.price_var.set(str(self.service.get('price', 0.0)))
        self.attachment_path = tk.StringVar(value=self.service.get('file_path', '') or '')
    
    def update_total(self, *args):
        """Update total price calculation"""
        try:
            quantity = int(self.quantity_var.get() or 0)
            price = float(self.price_var.get() or 0)
            total = quantity * price
            self.total_label.config(text=utils.format_currency(total))
        except ValueError:
            self.total_label.config(text="$0.00")
    
    def on_browse_attachment(self):
        path = utils.select_attachment_file()
        if path:
            self.attachment_path.set(path)
    
    def on_open_attachment(self):
        utils.open_if_exists(self.attachment_path.get())
    
    def on_ok(self):
        # Validate input
        name = self.name_var.get().strip()
        description = self.description_entry.get('1.0', tk.END).strip()
        quantity = self.quantity_var.get().strip()
        price = self.price_var.get().strip()
        
        if not name:
            utils.show_error("Validation Error", "Service name is required")
            return
        
        if not quantity or not utils.validate_int(quantity) or int(quantity) < 1:
            utils.show_error("Validation Error", "Quantity must be a positive integer")
            return
        
        if not price or not utils.validate_float(price) or float(price) < 0:
            utils.show_error("Validation Error", "Price must be a positive number")
            return
        
        self.result = {
            'name': name,
            'description': description,
            'quantity': int(quantity),
            'price': float(price),
            'file_path': self.attachment_path.get().strip() or None,
        }
        
        self.dialog.destroy()

class SparePartDialog(BaseDialog):
    """Dialog for adding spare parts to work orders"""
    def __init__(self, parent, part=None):
        self.part = part
        self.is_edit = part is not None
        title = "Edit Spare Part" if self.is_edit else "Add Spare Part"
        super().__init__(parent, title, (510, 420))
        
        if self.is_edit:
            self.load_part_data()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Part name
        ttk.Label(main_frame, text="Part Name:").grid(row=0, column=0, sticky=W, pady=5)
        self.name_var = tk.StringVar()
        self.name_combo = ttk.Combobox(main_frame, textvariable=self.name_var, width=40)
        self.name_combo['values'] = config.DEFAULT_PARTS
        self.name_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=1, column=0, sticky=NW, pady=5)
        self.description_entry = tk.Text(main_frame, width=30, height=4)
        self.description_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:").grid(row=2, column=0, sticky=W, pady=5)
        self.quantity_var = tk.StringVar(value="1")
        self.quantity_entry = utils.NumberEntry(main_frame, textvariable=self.quantity_var, 
                                               allow_decimal=False, width=40)
        self.quantity_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Price
        ttk.Label(main_frame, text="Unit Price ($):").grid(row=3, column=0, sticky=W, pady=5)
        self.price_var = tk.StringVar(value="0.00")
        self.price_entry = utils.NumberEntry(main_frame, textvariable=self.price_var, width=40)
        self.price_entry.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        # Total (calculated)
        ttk.Label(main_frame, text="Total:").grid(row=4, column=0, sticky=W, pady=5)
        self.total_label = ttk.Label(main_frame, text="$0.00", font=config.FONTS['header'])
        self.total_label.grid(row=4, column=1, sticky=W, pady=5, padx=(10, 0))
        
        # Attachment
        ttk.Label(main_frame, text="Attachment:").grid(row=5, column=0, sticky=W, pady=5)
        attach_frame = ttk.Frame(main_frame)
        attach_frame.grid(row=5, column=1, sticky=W, pady=5, padx=(10, 0))
        self.attachment_path = tk.StringVar()
        self.attachment_entry = ttk.Entry(attach_frame, textvariable=self.attachment_path, width=32)
        self.attachment_entry.pack(side=LEFT)
        ttk.Button(attach_frame, text="Browse", command=self.on_browse_attachment, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(attach_frame, text="Open", command=self.on_open_attachment, bootstyle=SECONDARY).pack(side=LEFT)
        
        # Bind events to update total
        self.quantity_var.trace('w', self.update_total)
        self.price_var.trace('w', self.update_total)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Add" if not self.is_edit else "Save", command=self.on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
    
    def load_part_data(self):
        """Load part data for editing"""
        self.name_var.set(self.part.get('name', ''))
        description = self.part.get('description', '')
        self.description_entry.insert('1.0', description)
        self.quantity_var.set(str(self.part.get('quantity', 1)))
        self.price_var.set(str(self.part.get('price', 0.0)))
        self.attachment_path = tk.StringVar(value=self.part.get('file_path', '') or '')
    
    def update_total(self, *args):
        """Update total price calculation"""
        try:
            quantity = int(self.quantity_var.get() or 0)
            price = float(self.price_var.get() or 0)
            total = quantity * price
            self.total_label.config(text=utils.format_currency(total))
        except ValueError:
            self.total_label.config(text="$0.00")
    
    def on_browse_attachment(self):
        path = utils.select_attachment_file()
        if path:
            self.attachment_path.set(path)
    
    def on_open_attachment(self):
        utils.open_if_exists(self.attachment_path.get())
    
    def on_ok(self):
        # Validate input
        name = self.name_var.get().strip()
        description = self.description_entry.get('1.0', tk.END).strip()
        quantity = self.quantity_var.get().strip()
        price = self.price_var.get().strip()
        
        if not name:
            utils.show_error("Validation Error", "Part name is required")
            return
        
        if not quantity or not utils.validate_int(quantity) or int(quantity) < 1:
            utils.show_error("Validation Error", "Quantity must be a positive integer")
            return
        
        if not price or not utils.validate_float(price) or float(price) < 0:
            utils.show_error("Validation Error", "Price must be a positive number")
            return
        
        self.result = {
            'name': name,
            'description': description,
            'quantity': int(quantity),
            'price': float(price),
            'file_path': self.attachment_path.get().strip() or None,
        }
        
        self.dialog.destroy()


class ServiceTemplateDialog(BaseDialog):
    """Dialog for adding/editing service templates"""

    def __init__(self, parent, db_manager, template=None):
        self.db_manager = db_manager
        self.template = template
        self.is_edit = template is not None
        title = "Edit Service Template" if self.is_edit else "Add Service Template"
        super().__init__(parent, title, (500, 400))

        if self.is_edit:
            self.load_template_data()

    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)

        # Service name
        ttk.Label(main_frame, text="Service Name:").grid(row=0, column=0, sticky=W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=50)
        self.name_entry.grid(row=0, column=1, pady=5, padx=(10, 0), sticky=W + E)
        self.name_entry.focus()

        # Category
        ttk.Label(main_frame, text="Category:").grid(row=1, column=0, sticky=W, pady=5)
        self.category_var = tk.StringVar(value="General")
        categories = ["General", "Engine", "Brakes", "Transmission", "Electrical", "Body", "Suspension"]
        self.category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, values=categories, width=47)
        self.category_combo.grid(row=1, column=1, pady=5, padx=(10, 0), sticky=W + E)

        # Description
        ttk.Label(main_frame, text="Description:").grid(row=2, column=0, sticky=NW, pady=5)
        self.description_entry = tk.Text(main_frame, width=35, height=5)
        self.description_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky=W + E)

        # Default price
        ttk.Label(main_frame, text="Default Price ($):").grid(row=3, column=0, sticky=W, pady=5)
        self.price_var = tk.StringVar(value="0.00")
        self.price_entry = utils.NumberEntry(main_frame, textvariable=self.price_var, width=50)
        self.price_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky=W + E)

        # Configure grid weights
        main_frame.grid_columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

    def load_template_data(self):
        """Load template data for editing"""
        self.name_var.set(self.template.get('name', ''))
        self.category_var.set(self.template.get('category', 'General'))
        description = self.template.get('description', '')
        self.description_entry.insert('1.0', description)
        self.price_var.set(str(self.template.get('default_price', 0.0)))

    def on_ok(self):
        # Validate input
        name = self.name_var.get().strip()
        category = self.category_var.get().strip()
        description = self.description_entry.get('1.0', tk.END).strip()
        price = self.price_var.get().strip()

        if not name:
            utils.show_error("Validation Error", "Service name is required")
            return

        if not category:
            utils.show_error("Validation Error", "Category is required")
            return

        if not price or not utils.validate_float(price) or float(price) < 0:
            utils.show_error("Validation Error", "Default price must be a positive number")
            return

        self.result = {
            'name': name,
            'category': category,
            'description': description,
            'default_price': float(price)
        }

        self.dialog.destroy()


class SparePartTemplateDialog(BaseDialog):
    """Dialog for adding/editing spare part templates"""

    def __init__(self, parent, db_manager, template=None):
        self.db_manager = db_manager
        self.template = template
        self.is_edit = template is not None
        title = "Edit Spare Part Template" if self.is_edit else "Add Spare Part Template"
        super().__init__(parent, title, (550, 500))

        if self.is_edit:
            self.load_template_data()

    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)

        # Part name
        ttk.Label(main_frame, text="Part Name:").grid(row=0, column=0, sticky=W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=50)
        self.name_entry.grid(row=0, column=1, pady=5, padx=(10, 0), sticky=W + E)
        self.name_entry.focus()

        # Category
        ttk.Label(main_frame, text="Category:").grid(row=1, column=0, sticky=W, pady=5)
        self.category_var = tk.StringVar(value="General")
        categories = ["General", "Engine", "Brakes", "Transmission", "Electrical", "Body", "Suspension", "Filters",
                      "Fluids"]
        self.category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, values=categories, width=47)
        self.category_combo.grid(row=1, column=1, pady=5, padx=(10, 0), sticky=W + E)

        # Part number
        ttk.Label(main_frame, text="Part Number:").grid(row=2, column=0, sticky=W, pady=5)
        self.part_number_var = tk.StringVar()
        self.part_number_entry = ttk.Entry(main_frame, textvariable=self.part_number_var, width=50)
        self.part_number_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky=W + E)

        # Supplier
        ttk.Label(main_frame, text="Supplier:").grid(row=3, column=0, sticky=W, pady=5)
        self.supplier_var = tk.StringVar()
        self.supplier_entry = ttk.Entry(main_frame, textvariable=self.supplier_var, width=50)
        self.supplier_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky=W + E)

        # Description
        ttk.Label(main_frame, text="Description:").grid(row=4, column=0, sticky=NW, pady=5)
        self.description_entry = tk.Text(main_frame, width=35, height=4)
        self.description_entry.grid(row=4, column=1, pady=5, padx=(10, 0), sticky=W + E)

        # Default price
        ttk.Label(main_frame, text="Default Price ($):").grid(row=5, column=0, sticky=W, pady=5)
        self.price_var = tk.StringVar(value="0.00")
        self.price_entry = utils.NumberEntry(main_frame, textvariable=self.price_var, width=50)
        self.price_entry.grid(row=5, column=1, pady=5, padx=(10, 0), sticky=W + E)

        # Configure grid weights
        main_frame.grid_columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

    def load_template_data(self):
        """Load template data for editing"""
        self.name_var.set(self.template.get('name', ''))
        self.category_var.set(self.template.get('category', 'General'))
        self.part_number_var.set(self.template.get('part_number', ''))
        self.supplier_var.set(self.template.get('supplier', ''))
        description = self.template.get('description', '')
        self.description_entry.insert('1.0', description)
        self.price_var.set(str(self.template.get('default_price', 0.0)))

    def on_ok(self):
        # Validate input
        name = self.name_var.get().strip()
        category = self.category_var.get().strip()
        part_number = self.part_number_var.get().strip()
        supplier = self.supplier_var.get().strip()
        description = self.description_entry.get('1.0', tk.END).strip()
        price = self.price_var.get().strip()

        if not name:
            utils.show_error("Validation Error", "Part name is required")
            return

        if not category:
            utils.show_error("Validation Error", "Category is required")
            return

        if not price or not utils.validate_float(price) or float(price) < 0:
            utils.show_error("Validation Error", "Default price must be a positive number")
            return

        self.result = {
            'name': name,
            'category': category,
            'part_number': part_number,
            'supplier': supplier,
            'description': description,
            'default_price': float(price)
        }

        self.dialog.destroy()

"""
Frame implementations for the Vehicle Repair Workshop Management System
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from datetime import datetime, timedelta
import os
from pathlib import Path

import config
import utils
from dialogs import *
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class BaseFrame(ttk.Frame):
    """Base class for all application frames"""
    
    def __init__(self, parent, db_manager, app):
        super().__init__(parent)
        self.db_manager = db_manager
        self.app = app
        self.setup_frame()
    
    def setup_frame(self):
        """Override in subclasses"""
        pass
    
    def refresh(self):
        """Override in subclasses to refresh frame data"""
        pass

class CustomersFrame(BaseFrame):
    """Frame for customer management"""
    
    def setup_frame(self):
        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Customer Management", 
                               font=config.FONTS['title'])
        title_label.pack(anchor=W, pady=(0, 10))
        
        # Search and buttons frame
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=(0, 10))
        
        # Search
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=LEFT)
        
        ttk.Label(search_frame, text="Search:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=RIGHT)
        
        ttk.Button(button_frame, text="Add Customer", command=self.add_customer,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Edit", command=self.edit_customer,
                  bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Delete", command=self.delete_customer,
                  bootstyle=DANGER).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Refresh", command=self.refresh,
                  bootstyle=SUCCESS).pack(side=LEFT, padx=2)
        
        # Treeview for customers
        self.create_treeview(main_frame)
        
        # Load initial data
        self.refresh()
    
    def create_treeview(self, parent):
        """Create the customers treeview"""
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)
        
        columns = ('ID', 'Name', 'Phone', 'Address', 'Created')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Phone', text='Phone')
        self.tree.heading('Address', text='Address')
        self.tree.heading('Created', text='Created')
        
        # Define column widths
        self.tree.column('ID', width=50)
        self.tree.column('Name', width=200)
        self.tree.column('Phone', width=150)
        self.tree.column('Address', width=300)
        self.tree.column('Created', width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Bind double-click to edit
        self.tree.bind('<Double-1>', lambda e: self.edit_customer())
    
    def refresh(self):
        """Refresh customer data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load customers
        search_term = self.search_var.get().strip()
        if search_term:
            customers = self.db_manager.search_customers(search_term)
        else:
            customers = self.db_manager.get_customers()
        
        # Populate treeview
        for customer in customers:
            created_date = utils.format_date(customer['created_at'][:10]) if customer['created_at'] else ''
            self.tree.insert('', END, values=(
                customer['id'],
                customer['name'],
                customer['phone'],
                utils.truncate_text(customer['address'] or '', 40),
                created_date
            ))
    
    def on_search(self, *args):
        """Handle search input"""
        self.refresh()
    
    def add_customer(self):
        """Add new customer"""
        dialog = CustomerDialog(self)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                self.db_manager.add_customer(
                    dialog.result['name'],
                    dialog.result['phone'],
                    dialog.result['address']
                )
                utils.show_info("Success", "Customer added successfully")
                self.refresh()
            except Exception as e:
                utils.show_error("Error", f"Failed to add customer: {e}")
    
    def edit_customer(self):
        """Edit selected customer"""
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a customer to edit")
            return
        
        # Get customer data
        item = self.tree.item(selection[0])
        customer_id = item['values'][0]
        
        # Get full customer data from database
        customers = self.db_manager.get_customers()
        customer_data = None
        for customer in customers:
            if customer['id'] == customer_id:
                customer_data = customer
                break
        
        if not customer_data:
            utils.show_error("Error", "Customer not found")
            return
        
        dialog = CustomerDialog(self, customer_data)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                self.db_manager.update_customer(
                    customer_id,
                    dialog.result['name'],
                    dialog.result['phone'],
                    dialog.result['address']
                )
                utils.show_info("Success", "Customer updated successfully")
                self.refresh()
            except Exception as e:
                utils.show_error("Error", f"Failed to update customer: {e}")
    
    def delete_customer(self):
        """Delete selected customer"""
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a customer to delete")
            return
        
        item = self.tree.item(selection[0])
        customer_name = item['values'][1]
        customer_id = item['values'][0]
        
        if utils.ask_yes_no("Confirm Delete", 
                           f"Are you sure you want to delete customer '{customer_name}'?\n\n"
                           "This action cannot be undone."):
            try:
                self.db_manager.delete_customer(customer_id)
                utils.show_info("Success", "Customer deleted successfully")
                self.refresh()
            except Exception as e:
                utils.show_error("Error", f"Failed to delete customer: {e}")

class VehiclesFrame(BaseFrame):
    """Frame for vehicle management"""
    
    def setup_frame(self):
        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Vehicle Management", 
                               font=config.FONTS['title'])
        title_label.pack(anchor=W, pady=(0, 10))
        
        # Search and buttons frame
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=(0, 10))
        
        # Search
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=LEFT)
        
        ttk.Label(search_frame, text="Search:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=RIGHT)
        
        ttk.Button(button_frame, text="Add Vehicle", command=self.add_vehicle,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Edit", command=self.edit_vehicle,
                  bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Delete", command=self.delete_vehicle,
                  bootstyle=DANGER).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Refresh", command=self.refresh,
                  bootstyle=SUCCESS).pack(side=LEFT, padx=2)
        
        # Treeview for vehicles
        self.create_treeview(main_frame)
        
        # Load initial data
        self.refresh()
    
    def create_treeview(self, parent):
        """Create the vehicles treeview"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)
        
        columns = ('ID', 'License Plate', 'Brand', 'Model', 'Customer', 'Phone')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('License Plate', text='License Plate')
        self.tree.heading('Brand', text='Brand')
        self.tree.heading('Model', text='Model')
        self.tree.heading('Customer', text='Customer')
        self.tree.heading('Phone', text='Phone')
        
        # Define column widths
        self.tree.column('ID', width=50)
        self.tree.column('License Plate', width=120)
        self.tree.column('Brand', width=120)
        self.tree.column('Model', width=120)
        self.tree.column('Customer', width=200)
        self.tree.column('Phone', width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Bind double-click to edit
        self.tree.bind('<Double-1>', lambda e: self.edit_vehicle())
    
    def refresh(self):
        """Refresh vehicle data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load vehicles
        search_term = self.search_var.get().strip()
        if search_term:
            vehicles = self.db_manager.search_vehicles(search_term)
        else:
            vehicles = self.db_manager.get_vehicles()
        
        # Populate treeview
        for vehicle in vehicles:
            self.tree.insert('', END, values=(
                vehicle['id'],
                vehicle['license_plate'],
                vehicle['brand'],
                vehicle['model'],
                vehicle['customer_name'],
                vehicle['customer_phone']
            ))
    
    def on_search(self, *args):
        """Handle search input"""
        self.refresh()
    
    def add_vehicle(self):
        """Add new vehicle"""
        dialog = VehicleDialog(self, self.db_manager)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                self.db_manager.add_vehicle(
                    dialog.result['license_plate'],
                    dialog.result['brand'],
                    dialog.result['model'],
                    dialog.result['customer_phone']
                )
                utils.show_info("Success", "Vehicle added successfully")
                self.refresh()
            except Exception as e:
                utils.show_error("Error", f"Failed to add vehicle: {e}")
    
    def edit_vehicle(self):
        """Edit selected vehicle"""
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a vehicle to edit")
            return
        
        # Get vehicle data
        item = self.tree.item(selection[0])
        vehicle_id = item['values'][0]
        
        # Get full vehicle data from database
        vehicles = self.db_manager.get_vehicles()
        vehicle_data = None
        for vehicle in vehicles:
            if vehicle['id'] == vehicle_id:
                vehicle_data = vehicle
                break
        
        if not vehicle_data:
            utils.show_error("Error", "Vehicle not found")
            return
        
        dialog = VehicleDialog(self, self.db_manager, vehicle_data)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                self.db_manager.update_vehicle(
                    vehicle_id,
                    dialog.result['license_plate'],
                    dialog.result['brand'],
                    dialog.result['model'],
                    dialog.result['customer_phone']
                )
                utils.show_info("Success", "Vehicle updated successfully")
                self.refresh()
            except Exception as e:
                utils.show_error("Error", f"Failed to update vehicle: {e}")
    
    def delete_vehicle(self):
        """Delete selected vehicle"""
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a vehicle to delete")
            return
        
        item = self.tree.item(selection[0])
        license_plate = item['values'][1]
        vehicle_id = item['values'][0]
        
        if utils.ask_yes_no("Confirm Delete", 
                           f"Are you sure you want to delete vehicle '{license_plate}'?\n\n"
                           "This action cannot be undone."):
            try:
                self.db_manager.delete_vehicle(vehicle_id)
                utils.show_info("Success", "Vehicle deleted successfully")
                self.refresh()
            except Exception as e:
                utils.show_error("Error", f"Failed to delete vehicle: {e}")

class WorkOrdersFrame(BaseFrame):
    """Frame for work order management"""
    
    def setup_frame(self):
        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Work Order Management", 
                               font=config.FONTS['title'])
        title_label.pack(anchor=W, pady=(0, 10))
        
        # Search, service type, status filter and buttons frame
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=(0, 10))

        # Left: Search + Service Type + Status
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side=LEFT)

        # Search
        ttk.Label(filter_frame, text="Search:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=LEFT, padx=(0, 5))
        ttk.Button(filter_frame, text="Search", command=self.refresh, bootstyle=INFO).pack(side=LEFT, padx=(0, 10))

        # Service type filter
        ttk.Label(filter_frame, text="Service Type:").pack(side=LEFT, padx=(0, 5))
        self.service_type_var = tk.StringVar(value="All Services")
        self.service_type_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.service_type_var,
            values=["All Services", "Preventive", "Corrective", "Inspection"],
            width=18
        )
        self.service_type_combo.pack(side=LEFT, padx=(0, 10))
        self.service_type_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        # Status filter (existing)
        ttk.Label(filter_frame, text="Status:").pack(side=LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                   values=["All", "Open", "In Progress", "Completed"], width=15)
        filter_combo.pack(side=LEFT, padx=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())
        
        # Buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=RIGHT)
        
        ttk.Button(button_frame, text="New Order", command=self.add_work_order,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="View Details", command=self.view_details,
                  bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Update Status", command=self.update_status,
                  bootstyle=WARNING).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Refresh", command=self.refresh,
                  bootstyle=SUCCESS).pack(side=LEFT, padx=2)
        
        # Treeview for work orders
        self.create_treeview(main_frame)
        
        # Load initial data
        self.refresh()
    
    def create_treeview(self, parent):
        """Create the work orders treeview"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)
        
        columns = ('ID', 'License Plate', 'Customer', 'Entry Date', 'Status', 'Total Cost', 'Payment')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('License Plate', text='License Plate')
        self.tree.heading('Customer', text='Customer')
        self.tree.heading('Entry Date', text='Entry Date')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Total Cost', text='Total Cost')
        self.tree.heading('Payment', text='Payment')
        
        # Define column widths
        self.tree.column('ID', width=50)
        self.tree.column('License Plate', width=120)
        self.tree.column('Customer', width=150)
        self.tree.column('Entry Date', width=100)
        self.tree.column('Status', width=100)
        self.tree.column('Total Cost', width=100)
        self.tree.column('Payment', width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Bind double-click to view details
        self.tree.bind('<Double-1>', lambda e: self.view_details())
    
    def refresh(self):
        """Refresh work order data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Collect filters
        keyword = self.search_var.get().strip()
        service_type = self.service_type_var.get().strip()
        if service_type == "All Services":
            service_type = None

        # Load work orders using combined filters
        if keyword or service_type:
            work_orders = self.db_manager.filter_work_orders(keyword=keyword, service_type=service_type)
        else:
            work_orders = self.db_manager.get_work_orders()

        # Apply status filter last
        filter_status = self.filter_var.get()
        if filter_status != "All":
            work_orders = [wo for wo in work_orders if wo['status'] == filter_status]
        
        # Populate treeview
        for wo in work_orders:
            entry_date = utils.format_date(wo['entry_date']) if wo['entry_date'] else ''
            self.tree.insert('', END, values=(
                wo['id'],
                wo['license_plate'],
                wo['customer_name'],
                entry_date,
                wo['status'],
                utils.format_currency(wo['total_cost'] or 0),
                wo['payment_status']
            ))
    
    def add_work_order(self):
        """Add new work order"""
        dialog = WorkOrderDialog(self, self.db_manager)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                work_order_id = self.db_manager.add_work_order(
                    dialog.result['vehicle_id'],
                    dialog.result['entry_date'],
                    dialog.result['status']
                )
                utils.show_info("Success", "Work order created successfully")
                self.refresh()
                
                # Ask if user wants to add services/parts
                if utils.ask_yes_no("Add Services/Parts", 
                                   "Would you like to add services or parts to this work order?"):
                    self.view_details_by_id(work_order_id)
                    
            except Exception as e:
                utils.show_error("Error", f"Failed to create work order: {e}")
    
    def view_details(self):
        """View work order details"""
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a work order to view")
            return
        
        item = self.tree.item(selection[0])
        work_order_id = item['values'][0]
        self.view_details_by_id(work_order_id)
    
    def view_details_by_id(self, work_order_id):
        """View details for specific work order ID"""
        details_window = WorkOrderDetailsWindow(self, self.db_manager, work_order_id)
        self.wait_window(details_window.window)
        self.refresh()  # Refresh in case costs were updated
    
    def update_status(self):
        """Update work order status"""
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a work order to update")
            return
        
        item = self.tree.item(selection[0])
        work_order_id = item['values'][0]
        current_status = item['values'][4]
        
        # Create status update dialog
        dialog = StatusUpdateDialog(self, current_status)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                self.db_manager.update_work_order_status(work_order_id, dialog.result['status'])
                if 'payment_status' in dialog.result:
                    self.db_manager.update_work_order_payment_status(work_order_id, dialog.result['payment_status'])
                
                utils.show_info("Success", "Status updated successfully")
                self.refresh()
            except Exception as e:
                utils.show_error("Error", f"Failed to update status: {e}")

class InvoicesFrame(BaseFrame):
    """Frame for invoice management"""
    
    def setup_frame(self):
        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Invoice Management", 
                               font=config.FONTS['title'])
        title_label.pack(anchor=W, pady=(0, 10))
        
        # Search and buttons frame
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=X, pady=(0, 10))
        
        # Search
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=LEFT)
        
        ttk.Label(search_frame, text="Search:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=RIGHT)
        
        ttk.Button(button_frame, text="Create Invoice", command=self.create_invoice,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Mark as Paid", command=lambda: self.update_status('Paid'),
                  bootstyle=SUCCESS).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Mark as Unpaid", command=lambda: self.update_status('Unpaid'),
                  bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Refresh", command=self.refresh,
                  bootstyle=SUCCESS).pack(side=LEFT, padx=2)
        
        # Treeview for invoices
        self.create_treeview(main_frame)
        
        # Load initial data
        self.refresh()
    
    def create_treeview(self, parent):
        """Create the invoices treeview"""
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)
        
        columns = ('ID', 'Work Order', 'Date', 'Amount', 'Status', 'Customer', 'Phone')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('Work Order', text='Work Order')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Amount', text='Amount')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Customer', text='Customer')
        self.tree.heading('Phone', text='Phone')
        
        # Define column widths
        self.tree.column('ID', width=50)
        self.tree.column('Work Order', width=100)
        self.tree.column('Date', width=100)
        self.tree.column('Amount', width=100)
        self.tree.column('Status', width=100)
        self.tree.column('Customer', width=200)
        self.tree.column('Phone', width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Bind double-click to mark as paid
        self.tree.bind('<Double-1>', lambda e: self.update_status('Paid'))
    
    def refresh(self):
        """Refresh invoice data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load invoices
        invoices = self.db_manager.get_invoices()
        
        # Populate treeview
        for inv in invoices:
            self.tree.insert('', END, values=(
                inv['id'],
                inv['work_order_id'],
                utils.format_date(inv['invoice_date'][:10]) if inv['invoice_date'] else '',
                utils.format_currency(inv['total_amount']),
                inv['status'],
                inv['customer_name'],
                inv['customer_phone']
            ))
    
    def on_search(self, *args):
        self.refresh()
    
    def create_invoice(self):
        """Create invoice from selected work order"""
        utils.show_warning("Not Implemented", "Creating invoices directly is not available here.")
    
    def update_status(self, status):
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select an invoice")
            return
        
        item = self.tree.item(selection[0])
        invoice_id = item['values'][0]
        
        try:
            self.db_manager.update_invoice_status(invoice_id, status)
            utils.show_info("Success", f"Invoice marked as {status}")
            self.refresh()
        except Exception as e:
            utils.show_error("Error", f"Failed to update status: {e}")

class AppointmentsFrame(BaseFrame):
    """Frame for appointment management"""
    
    def setup_frame(self):
        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Appointment Management", 
                               font=config.FONTS['title'])
        title_label.pack(anchor=W, pady=(0, 10))
        
        # Input fields frame
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=X, pady=(0, 10))
        
        # ID (read-only)
        ttk.Label(fields_frame, text="ID:").grid(row=0, column=0, sticky=W, pady=5)
        self.id_var = tk.StringVar()
        self.id_entry = ttk.Entry(fields_frame, textvariable=self.id_var, width=10, state='readonly')
        self.id_entry.grid(row=0, column=1, pady=5, padx=(10, 20), sticky=W)
        
        # Name
        ttk.Label(fields_frame, text="Name:").grid(row=0, column=2, sticky=W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(fields_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=0, column=3, pady=5, padx=(10, 20), sticky=W)
        
        # Date (DatePicker)
        ttk.Label(fields_frame, text="Date:").grid(row=0, column=4, sticky=W, pady=5)
        self.date_var = tk.StringVar()
        # Try to use ttkbootstrap DateEntry, fallback to Entry
        try:
            from ttkbootstrap.widgets import DateEntry
            self.date_entry = DateEntry(fields_frame, textvariable=self.date_var, width=18, bootstyle=PRIMARY)
        except Exception:
            self.date_entry = ttk.Entry(fields_frame, textvariable=self.date_var, width=20)
        self.date_entry.grid(row=0, column=5, pady=5, padx=(10, 0), sticky=W)
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
        
        # Description (multi-line)
        ttk.Label(fields_frame, text="Description:").grid(row=1, column=0, sticky=NW, pady=5)
        self.description_text = tk.Text(fields_frame, width=80, height=4)
        self.description_text.grid(row=1, column=1, columnspan=5, pady=5, padx=(10, 0), sticky=W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(0, 10))
        ttk.Button(button_frame, text="Create", command=self.create_appointment, bootstyle=PRIMARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Read", command=self.read_appointment, bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Update", command=self.update_appointment, bootstyle=INFO).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Delete", command=self.delete_appointment, bootstyle=DANGER).pack(side=LEFT, padx=2)
        ttk.Button(button_frame, text="Clear/Reset", command=self.clear_fields, bootstyle=WARNING).pack(side=LEFT, padx=2)
        
        # Treeview for appointments
        self.create_treeview(main_frame)
        
        # Load initial data
        self.refresh()
        
    def create_treeview(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)
        
        columns = ('ID', 'Name', 'Description', 'Date')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=16)
        
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Description', text='Description')
        self.tree.heading('Date', text='Date')
        
        self.tree.column('ID', width=60)
        self.tree.column('Name', width=220)
        self.tree.column('Description', width=500)
        self.tree.column('Date', width=120)
        
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
    
    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        appointments = self.db_manager.get_appointments()
        for appt in appointments:
            self.tree.insert('', END, values=(
                appt['id'],
                appt['name'],
                utils.truncate_text(appt['description'] or '', 80),
                utils.format_date(appt['date'][:10]) if appt['date'] else ''
            ))
    
    def on_tree_select(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item['values']
        self.id_var.set(values[0])
        self.name_var.set(values[1])
        # Fetch full description from DB in case it was truncated
        try:
            appt_id = int(values[0])
            full = [a for a in self.db_manager.get_appointments() if a['id'] == appt_id]
            desc = full[0]['description'] if full else values[2]
        except Exception:
            desc = values[2]
        self.description_text.delete('1.0', tk.END)
        self.description_text.insert('1.0', desc or '')
        # store date as YYYY-MM-DD
        date_raw = values[3]
        try:
            # if formatted like MM/DD/YYYY -> convert back
            date_obj = datetime.strptime(date_raw, '%m/%d/%Y')
            self.date_var.set(date_obj.strftime('%Y-%m-%d'))
        except Exception:
            self.date_var.set(date_raw)
    
    def clear_fields(self):
        self.id_var.set("")
        self.name_var.set("")
        self.description_text.delete('1.0', tk.END)
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
    
    def create_appointment(self):
        name = self.name_var.get().strip()
        description = self.description_text.get('1.0', tk.END).strip()
        date_str = self.date_var.get().strip()
        if not name:
            utils.show_error("Validation Error", "Name is required")
            return
        if not date_str:
            utils.show_error("Validation Error", "Date is required")
            return
        try:
            # normalize to YYYY-MM-DD
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                date_norm = dt.strftime('%Y-%m-%d')
            except ValueError:
                dt = datetime.strptime(date_str, '%m/%d/%Y')
                date_norm = dt.strftime('%Y-%m-%d')
            self.db_manager.add_appointment(name, description, date_norm)
            utils.show_info("Success", "Appointment created")
            self.refresh()
            self.clear_fields()
        except Exception as e:
            utils.show_error("Error", f"Failed to create appointment: {e}")
    
    def read_appointment(self):
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select an appointment to read")
            return
        item = self.tree.item(selection[0])
        appt_id, name, _, date_disp = item['values']
        # Fetch full row
        appts = self.db_manager.get_appointments()
        row = next((a for a in appts if a['id'] == appt_id), None)
        description = row['description'] if row else ''
        utils.show_info("Appointment Details", f"ID: {appt_id}\nName: {name}\nDate: {date_disp}\n\nDescription:\n{description}")
    
    def update_appointment(self):
        appt_id = self.id_var.get().strip()
        if not appt_id:
            utils.show_warning("No Selection", "Please select an appointment to update")
            return
        name = self.name_var.get().strip()
        description = self.description_text.get('1.0', tk.END).strip()
        date_str = self.date_var.get().strip()
        if not name:
            utils.show_error("Validation Error", "Name is required")
            return
        if not date_str:
            utils.show_error("Validation Error", "Date is required")
            return
        try:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                date_norm = dt.strftime('%Y-%m-%d')
            except ValueError:
                dt = datetime.strptime(date_str, '%m/%d/%Y')
                date_norm = dt.strftime('%Y-%m-%d')
            self.db_manager.update_appointment(int(appt_id), name, description, date_norm)
            utils.show_info("Success", "Appointment updated")
            self.refresh()
        except Exception as e:
            utils.show_error("Error", f"Failed to update appointment: {e}")
    
    def delete_appointment(self):
        appt_id = self.id_var.get().strip()
        if not appt_id:
            selection = self.tree.selection()
            if selection:
                item = self.tree.item(selection[0])
                appt_id = str(item['values'][0])
        if not appt_id:
            utils.show_warning("No Selection", "Please select an appointment to delete")
            return
        if utils.ask_yes_no("Confirm Delete", "Are you sure you want to delete this appointment?\n\nThis action cannot be undone."):
            try:
                self.db_manager.delete_appointment(int(appt_id))
                utils.show_info("Success", "Appointment deleted")
                self.refresh()
                self.clear_fields()
            except Exception as e:
                utils.show_error("Error", f"Failed to delete appointment: {e}")

class ReportsFrame(BaseFrame):
    """Frame for reports and statistics"""
    
    def setup_frame(self):
        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Reports and Statistics", 
                               font=config.FONTS['title'])
        title_label.pack(anchor=W, pady=(0, 10))
        
        # Date range selection
        range_frame = ttk.Frame(main_frame)
        range_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Label(range_frame, text="Date Range:").pack(side=LEFT, padx=(0, 10))
        
        self.date_range_var = tk.StringVar(value="This Month")
        date_combo = ttk.Combobox(range_frame, textvariable=self.date_range_var, width=20)
        date_ranges = utils.get_date_range_options()
        date_combo['values'] = [option[0] for option in date_ranges]
        date_combo.pack(side=LEFT, padx=(0, 10))
        date_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_overview())
        
        ttk.Button(range_frame, text="Refresh", command=self.refresh_overview,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=10)
        
        # Statistics display
        self.stats_frame = ttk.Frame(main_frame)
        self.stats_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.refresh_overview()
    
    def refresh_overview(self):
        """Refresh overview statistics"""
        # Clear existing widgets
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Get date range
        selected_range = self.date_range_var.get()
        date_ranges = utils.get_date_range_options()
        start_date, end_date = None, None
        
        for option in date_ranges:
            if option[0] == selected_range:
                start_date, end_date = option[1], option[2]
                break
        
        # Get statistics
        stats = self.db_manager.get_repair_statistics(start_date, end_date)
        
        # Create statistics cards
        cards_frame = ttk.Frame(self.stats_frame)
        cards_frame.pack(fill=X, pady=(0, 20))

        # Total orders card
        self.create_stat_card(cards_frame, "Total Orders", str(stats.get('total_orders', 0)), 
                             "📋", row=0, col=0)
        
        # Completed orders card
        self.create_stat_card(cards_frame, "Completed", str(stats.get('completed_orders', 0)),
                             "✅", row=0, col=1)
        
        # Open orders card
        self.create_stat_card(cards_frame, "Open Orders", str(stats.get('open_orders', 0)), 
                             "🔧", row=0, col=2)
        
        # Total revenue card
        revenue = stats.get('total_revenue', 0) or 0
        self.create_stat_card(cards_frame, "Total Revenue", utils.format_currency(revenue), 
                             "💰", row=1, col=0)
        
        # Average order value card
        avg_value = stats.get('avg_order_value', 0) or 0
        self.create_stat_card(cards_frame, "Avg Order Value", utils.format_currency(avg_value), 
                             "📊", row=1, col=1)
        
        # Configure grid weights
        for i in range(3):
            cards_frame.grid_columnconfigure(i, weight=1)
    
    def create_stat_card(self, parent, title, value, icon, row, col):
        """Create a statistics card"""
        card = ttk.Frame(parent, style='', padding=20)
        """" style= 'light.TFrame' """
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Icon and title
        header_frame = ttk.Frame(card, style='')
        """" style= 'light.TFrame' """
        header_frame.pack(fill=X)
        
        ttk.Label(header_frame, text=icon, font=('Arial', 20), style='info.TLabel').pack(side=LEFT)
        ttk.Label(header_frame, text=title, font=config.FONTS['header'], 
                 style='info.TLabel').pack(side=LEFT, padx=(10, 0))
        
        # Value
        ttk.Label(card, text=value, font=('Arial', 24, 'bold'), 
                 style='info.TLabel').pack(pady=(10, 0))
    
    def create_revenue_tab(self, notebook):
        """Create revenue statistics tab"""
        revenue_frame = ttk.Frame(notebook)
        notebook.add(revenue_frame, text="Revenue")
        
        # Period selection
        period_frame = ttk.Frame(revenue_frame)
        period_frame.pack(fill=X, padx=10, pady=10)
        
        ttk.Label(period_frame, text="Period:").pack(side=LEFT, padx=(0, 10))
        
        self.period_var = tk.StringVar(value="monthly")
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var, 
                                   values=["daily", "monthly", "yearly"], width=15)
        period_combo.pack(side=LEFT, padx=(0, 10))
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_revenue())
        
        ttk.Button(period_frame, text="Refresh", command=self.refresh_revenue,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=10)
        
        # Revenue table
        self.create_revenue_table(revenue_frame)
        
        self.refresh_revenue()
    
    def create_revenue_table(self, parent):
        """Create revenue statistics table"""
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Period', 'Orders', 'Revenue', 'Avg Order Value')
        self.revenue_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.revenue_tree.heading('Period', text='Period')
        self.revenue_tree.heading('Orders', text='Orders')
        self.revenue_tree.heading('Revenue', text='Revenue')
        self.revenue_tree.heading('Avg Order Value', text='Avg Order Value')
        
        # Define column widths
        self.revenue_tree.column('Period', width=150)
        self.revenue_tree.column('Orders', width=100)
        self.revenue_tree.column('Revenue', width=150)
        self.revenue_tree.column('Avg Order Value', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.revenue_tree.yview)
        self.revenue_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.revenue_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def refresh_revenue(self):
        """Refresh revenue statistics"""
        # Clear existing items
        for item in self.revenue_tree.get_children():
            self.revenue_tree.delete(item)
        
        # Get revenue data
        period = self.period_var.get()
        revenue_data = self.db_manager.get_revenue_by_period(period)
        
        # Populate table
        for data in revenue_data:
            self.revenue_tree.insert('', END, values=(
                data['period'],
                data['order_count'],
                utils.format_currency(data['revenue'] or 0),
                utils.format_currency(data['avg_order_value'] or 0)
            ))
    
    def create_services_tab(self, notebook):
        """Create services statistics tab"""
        services_frame = ttk.Frame(notebook)
        notebook.add(services_frame, text="Top Services")
        
        # Refresh button
        ttk.Button(services_frame, text="Refresh", command=self.refresh_services,
                  bootstyle=PRIMARY).pack(anchor=W, padx=10, pady=10)
        
        # Services table
        self.create_services_table(services_frame)
        
        self.refresh_services()
    
    def create_services_table(self, parent):
        """Create services statistics table"""
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Service', 'Usage Count', 'Total Quantity')
        self.services_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.services_tree.heading('Service', text='Service')
        self.services_tree.heading('Usage Count', text='Usage Count')
        self.services_tree.heading('Total Quantity', text='Total Quantity')
        
        # Define column widths
        self.services_tree.column('Service', width=300)
        self.services_tree.column('Usage Count', width=150)
        self.services_tree.column('Total Quantity', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.services_tree.yview)
        self.services_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.services_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def refresh_services(self):
        """Refresh services statistics"""
        # Clear existing items
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
        
        # Get statistics
        stats = self.db_manager.get_repair_statistics()
        top_services = stats.get('top_services', [])
        
        # Populate table
        for service in top_services:
            self.services_tree.insert('', END, values=(
                service['name'],
                service['usage_count'],
                service['total_quantity']
            ))
    
    def create_customers_tab(self, notebook):
        """Create customers statistics tab"""
        customers_frame = ttk.Frame(notebook)
        notebook.add(customers_frame, text="Top Customers")
        
        # Refresh button
        ttk.Button(customers_frame, text="Refresh", command=self.refresh_customers,
                  bootstyle=PRIMARY).pack(anchor=W, padx=10, pady=10)
        
        # Customers table
        self.create_customers_table(customers_frame)
        
        self.refresh_customers()
    
    def create_customers_table(self, parent):
        """Create customers statistics table"""
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Customer', 'Phone', 'Orders', 'Total Spent')
        self.customers_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.customers_tree.heading('Customer', text='Customer')
        self.customers_tree.heading('Phone', text='Phone')
        self.customers_tree.heading('Orders', text='Orders')
        self.customers_tree.heading('Total Spent', text='Total Spent')
        
        # Define column widths
        self.customers_tree.column('Customer', width=200)
        self.customers_tree.column('Phone', width=150)
        self.customers_tree.column('Orders', width=100)
        self.customers_tree.column('Total Spent', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.customers_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
    
    def refresh_customers(self):
        """Refresh customers statistics"""
        # Clear existing items
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Get statistics
        stats = self.db_manager.get_repair_statistics()
        top_customers = stats.get('top_customers', [])
        
        # Populate table
        for customer in top_customers:
            self.customers_tree.insert('', END, values=(
                customer['name'],
                customer['phone'],
                customer['order_count'],
                utils.format_currency(customer['total_spent'] or 0)
            ))

class SettingsFrame(BaseFrame):
    """Frame for application settings"""
    
    def setup_frame(self):
        # Create main container with scrollable content
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = scrollable_frame
        main_frame = ttk.Frame(main_frame, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Application Settings", 
                               font=config.FONTS['title'])
        title_label.pack(anchor=W, pady=(0, 20))
        
        # Appearance settings
        self.create_appearance_section(main_frame)
        
        # Company settings
        self.create_company_section(main_frame)
        
        # Load current settings
        self.load_settings()
    
    def create_appearance_section(self, parent):
        """Create appearance settings section"""
        # Appearance frame
        appearance_frame = ttk.LabelFrame(parent, text="Appearance Settings", padding=15)
        appearance_frame.pack(fill=X, pady=(0, 20))
        
        # Theme selection
        theme_frame = ttk.Frame(appearance_frame)
        theme_frame.pack(fill=X, pady=5)
        
        ttk.Label(theme_frame, text="Theme:").pack(side=LEFT, padx=(0, 10))
        
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, width=20)
        # Available ttkbootstrap themes
        themes = ['flatly', 'litera', 'minty', 'lumen', 'sandstone', 'yeti', 'pulse', 
                 'united', 'morph', 'journal', 'darkly', 'superhero', 'solar', 'cyborg', 'vapor']
        theme_combo['values'] = themes
        theme_combo.pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(theme_frame, text="Apply Theme", command=self.apply_theme,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=10)
    
    def create_company_section(self, parent):
        """Create company settings section"""
        # Company frame
        company_frame = ttk.LabelFrame(parent, text="Company Information", padding=15)
        company_frame.pack(fill=X, pady=(0, 20))
        
        # Company name
        name_frame = ttk.Frame(company_frame)
        name_frame.pack(fill=X, pady=5)
        
        ttk.Label(name_frame, text="Company Name:").pack(side=LEFT, padx=(0, 10))
        self.company_name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.company_name_var, width=40)
        name_entry.pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(name_frame, text="Update", command=self.update_company_name,
                  bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        # Company logo
        logo_frame = ttk.Frame(company_frame)
        logo_frame.pack(fill=X, pady=10)
        
        ttk.Label(logo_frame, text="Company Logo:").pack(side=LEFT, padx=(0, 10))
        
        self.logo_label = ttk.Label(logo_frame, text="No logo selected")
        self.logo_label.pack(side=LEFT, padx=(0, 10))
        
        ttk.Button(logo_frame, text="Browse", command=self.browse_logo,
                  bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        ttk.Button(logo_frame, text="Remove", command=self.remove_logo,
                  bootstyle=DANGER).pack(side=LEFT, padx=5)
        
        # Logo preview
        self.logo_preview_frame = ttk.Frame(company_frame)
        self.logo_preview_frame.pack(fill=X, pady=10)
        
        # Database settings
        db_frame = ttk.LabelFrame(parent, text="Database", padding=15)
        db_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Button(db_frame, text="Backup Database", command=self.backup_database,
                  bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(db_frame, text="Export Data", command=self.export_data,
                  bootstyle=INFO).pack(side=LEFT, padx=5)
    
    def load_settings(self):
        """Load current settings"""
        # Load theme
        current_theme = self.db_manager.get_setting('theme', config.DEFAULT_THEME)
        self.theme_var.set(current_theme)
        
        # Load company name
        company_name = self.db_manager.get_setting('company_name', config.DEFAULT_COMPANY_NAME)
        self.company_name_var.set(company_name)
        
        # Load logo
        self.load_logo_preview()
    
    def apply_theme(self):
        """Apply selected theme"""
        selected_theme = self.theme_var.get()
        if selected_theme:
            self.app.update_theme(selected_theme)
    
    def update_company_name(self):
        """Update company name"""
        new_name = self.company_name_var.get().strip()
        if new_name:
            self.db_manager.set_setting('company_name', new_name)
            utils.show_info("Success", "Company name updated successfully")
            self.app.update_company_info()
        else:
            utils.show_error("Error", "Company name cannot be empty")
    
    def browse_logo(self):
        """Browse for logo file"""
        filename = utils.select_image_file()
        if filename:
            try:
                # Copy logo to logos directory
                logo_path = config.LOGOS_DIR / "logo.png"
                
                # Load and resize image
                image = Image.open(filename)
                image = image.resize((100, 100), Image.Resampling.LANCZOS)
                image.save(logo_path)
                
                utils.show_info("Success", "Logo updated successfully")
                self.load_logo_preview()
                
            except Exception as e:
                utils.show_error("Error", f"Failed to update logo: {e}")
    
    def remove_logo(self):
        """Remove company logo"""
        logo_path = config.LOGOS_DIR / "logo.png"
        if logo_path.exists():
            if utils.ask_yes_no("Confirm", "Are you sure you want to remove the company logo?"):
                try:
                    logo_path.unlink()
                    utils.show_info("Success", "Logo removed successfully")
                    self.load_logo_preview()
                except Exception as e:
                    utils.show_error("Error", f"Failed to remove logo: {e}")
        else:
            utils.show_info("Info", "No logo to remove")
    
    def load_logo_preview(self):
        """Load logo preview"""
        # Clear existing preview
        for widget in self.logo_preview_frame.winfo_children():
            widget.destroy()
        
        logo_path = config.LOGOS_DIR / "logo.png"
        if logo_path.exists():
            try:
                logo_image = utils.load_image(str(logo_path), (150, 75))
                if logo_image:
                    preview_label = ttk.Label(self.logo_preview_frame, image=logo_image)
                    preview_label.image = logo_image  # Keep reference
                    preview_label.pack()
                    self.logo_label.config(text="Logo loaded")
                else:
                    self.logo_label.config(text="Error loading logo")
            except Exception as e:
                self.logo_label.config(text="Error loading logo")
        else:
            self.logo_label.config(text="No logo selected")
    
    def backup_database(self):
        """Backup database"""
        filename = utils.save_file_dialog(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import shutil
                shutil.copy2(config.DB_PATH, filename)
                utils.show_info("Success", f"Database backed up to {filename}")
            except Exception as e:
                utils.show_error("Error", f"Failed to backup database: {e}")
    
    def export_data(self):
        """Export data to CSV"""
        filename = utils.save_file_dialog(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import csv
                
                # Export customers, vehicles, and work orders
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Customers
                    writer.writerow(['CUSTOMERS'])
                    writer.writerow(['ID', 'Name', 'Phone', 'Address', 'Created'])
                    customers = self.db_manager.get_customers()
                    for customer in customers:
                        writer.writerow([customer['id'], customer['name'], customer['phone'], 
                                       customer['address'], customer['created_at']])
                    
                    writer.writerow([])  # Empty row
                    
                    # Vehicles
                    writer.writerow(['VEHICLES'])
                    writer.writerow(['ID', 'License Plate', 'Brand', 'Model', 'Customer Phone', 'Created'])
                    vehicles = self.db_manager.get_vehicles()
                    for vehicle in vehicles:
                        writer.writerow([vehicle['id'], vehicle['license_plate'], vehicle['brand'], 
                                       vehicle['model'], vehicle['customer_phone'], vehicle['created_at']])
                    
                    writer.writerow([])  # Empty row
                    
                    # Work Orders
                    writer.writerow(['WORK ORDERS'])
                    writer.writerow(['ID', 'Vehicle ID', 'Entry Date', 'Status', 'Total Cost', 'Payment Status', 'Created'])
                    work_orders = self.db_manager.get_work_orders()
                    for wo in work_orders:
                        writer.writerow([wo['id'], wo['vehicle_id'], wo['entry_date'], wo['status'], 
                                       wo['total_cost'], wo['payment_status'], wo['created_at']])
                
                utils.show_info("Success", f"Data exported to {filename}")
                
            except Exception as e:
                utils.show_error("Error", f"Failed to export data: {e}")

# Additional dialog classes for work order management

class WorkOrderDetailsWindow:
    """Window for managing work order details"""
    
    def __init__(self, parent, db_manager, work_order_id):
        self.parent = parent
        self.db_manager = db_manager
        self.work_order_id = work_order_id
        
        self.window = tk.Toplevel(parent)
        self.window.title("Work Order Details")
        self.window.geometry("900x700")
        self.window.grab_set()
        self.window.transient(parent)
        
        utils.center_window(self.window, 900, 700)
        
        self.create_widgets()
        self.refresh()
    
    def create_widgets(self):
        """Create widgets for work order details window"""
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Work order info
        self.create_work_order_info(main_frame)
        
        # Services and parts notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, pady=10)
        
        # Services tab
        self.create_services_tab(notebook)
        
        # Parts tab
        self.create_parts_tab(notebook)
        
        # Total cost display
        self.create_total_section(main_frame)
    
    def create_work_order_info(self, parent):
        """Create work order information section"""
        info_frame = ttk.LabelFrame(parent, text="Work Order Information", padding=10)
        info_frame.pack(fill=X, pady=(0, 10))
        
        self.info_label = ttk.Label(info_frame, text="Loading...", font=config.FONTS['default'])
        self.info_label.pack()
    
    def create_services_tab(self, notebook):
        """Create services tab"""
        services_frame = ttk.Frame(notebook)
        notebook.add(services_frame, text="Services")
        
        # Buttons
        button_frame = ttk.Frame(services_frame)
        button_frame.pack(fill=X, pady=10)
        
        ttk.Button(button_frame, text="Add Service", command=self.add_service,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Service", command=self.remove_service,
                  bootstyle=DANGER).pack(side=LEFT, padx=5)
        
        # Services treeview
        columns = ('ID', 'Name', 'Description', 'Quantity', 'Price', 'Total')
        self.services_tree = ttk.Treeview(services_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.services_tree.heading(col, text=col)
            if col == 'Description':
                self.services_tree.column(col, width=200)
            else:
                self.services_tree.column(col, width=100)
        
        # Scrollbar for services
        services_scroll = ttk.Scrollbar(services_frame, orient=VERTICAL, command=self.services_tree.yview)
        self.services_tree.configure(yscrollcommand=services_scroll.set)
        
        self.services_tree.pack(side=LEFT, fill=BOTH, expand=True)
        services_scroll.pack(side=RIGHT, fill=Y)
    
    def create_parts_tab(self, notebook):
        """Create parts tab"""
        parts_frame = ttk.Frame(notebook)
        notebook.add(parts_frame, text="Spare Parts")
        
        # Buttons
        button_frame = ttk.Frame(parts_frame)
        button_frame.pack(fill=X, pady=10)
        
        ttk.Button(button_frame, text="Add Part", command=self.add_part,
                  bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Part", command=self.remove_part,
                  bootstyle=DANGER).pack(side=LEFT, padx=5)
        
        # Parts treeview
        columns = ('ID', 'Name', 'Description', 'Quantity', 'Price', 'Total')
        self.parts_tree = ttk.Treeview(parts_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.parts_tree.heading(col, text=col)
            if col == 'Description':
                self.parts_tree.column(col, width=200)
            else:
                self.parts_tree.column(col, width=100)
        
        # Scrollbar for parts
        parts_scroll = ttk.Scrollbar(parts_frame, orient=VERTICAL, command=self.parts_tree.yview)
        self.parts_tree.configure(yscrollcommand=parts_scroll.set)
        
        self.parts_tree.pack(side=LEFT, fill=BOTH, expand=True)
        parts_scroll.pack(side=RIGHT, fill=Y)
    
    def create_total_section(self, parent):
        """Create total cost section"""
        total_frame = ttk.Frame(parent)
        total_frame.pack(fill=X, pady=10)
        
        self.total_label = ttk.Label(total_frame, text="Total Cost: $0.00", 
                                    font=config.FONTS['title'])
        self.total_label.pack(side=RIGHT)
        
        ttk.Button(total_frame, text="Close", command=self.window.destroy,
                  bootstyle=SECONDARY).pack(side=LEFT)
    
    def refresh(self):
        """Refresh work order details"""
        # Get work order details
        work_order = self.db_manager.get_work_order_details(self.work_order_id)
        if work_order:
            info_text = (f"Work Order #{work_order['id']} - {work_order['license_plate']}\n"
                        f"Vehicle: {work_order['brand']} {work_order['model']}\n"
                        f"Customer: {work_order['customer_name']} ({work_order['customer_phone']})\n"
                        f"Entry Date: {utils.format_date(work_order['entry_date'])}\n"
                        f"Status: {work_order['status']} | Payment: {work_order['payment_status']}")
            self.info_label.config(text=info_text)
        
        # Refresh services
        self.refresh_services()
        
        # Refresh parts
        self.refresh_parts()
        
        # Update total
        self.update_total()
    
    def refresh_services(self):
        """Refresh services list"""
        # Clear existing items
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
        
        # Load services
        services = self.db_manager.get_services_by_work_order(self.work_order_id)
        for service in services:
            total = service['quantity'] * service['price']
            self.services_tree.insert('', END, values=(
                service['id'],
                service['name'],
                utils.truncate_text(service['description'] or '', 30),
                service['quantity'],
                utils.format_currency(service['price']),
                utils.format_currency(total)
            ))
    
    def refresh_parts(self):
        """Refresh parts list"""
        # Clear existing items
        for item in self.parts_tree.get_children():
            self.parts_tree.delete(item)
        
        # Load parts
        parts = self.db_manager.get_spare_parts_by_work_order(self.work_order_id)
        for part in parts:
            total = part['quantity'] * part['price']
            self.parts_tree.insert('', END, values=(
                part['id'],
                part['name'],
                utils.truncate_text(part['description'] or '', 30),
                part['quantity'],
                utils.format_currency(part['price']),
                utils.format_currency(total)
            ))
    
    def update_total(self):
        """Update total cost display"""
        total_cost = self.db_manager.calculate_work_order_total(self.work_order_id)
        self.total_label.config(text=f"Total Cost: {utils.format_currency(total_cost)}")
    
    def add_service(self):
        """Add service to work order"""
        dialog = ServiceDialog(self.window)
        self.window.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                self.db_manager.add_service(
                    self.work_order_id,
                    dialog.result['name'],
                    dialog.result['description'],
                    dialog.result['quantity'],
                    dialog.result['price']
                )
                utils.show_info("Success", "Service added successfully")
                self.refresh_services()
                self.update_total()
            except Exception as e:
                utils.show_error("Error", f"Failed to add service: {e}")
    
    def add_part(self):
        """Add part to work order"""
        dialog = SparePartDialog(self.window)
        self.window.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                self.db_manager.add_spare_part(
                    self.work_order_id,
                    dialog.result['name'],
                    dialog.result['description'],
                    dialog.result['quantity'],
                    dialog.result['price']
                )
                utils.show_info("Success", "Spare part added successfully")
                self.refresh_parts()
                self.update_total()
            except Exception as e:
                utils.show_error("Error", f"Failed to add spare part: {e}")
    
    def remove_service(self):
        """Remove selected service"""
        selection = self.services_tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a service to remove")
            return
        
        item = self.services_tree.item(selection[0])
        service_id = item['values'][0]
        service_name = item['values'][1]
        
        if utils.ask_yes_no("Confirm", f"Remove service '{service_name}'?"):
            try:
                self.db_manager.delete_service(service_id, self.work_order_id)
                utils.show_info("Success", "Service removed successfully")
                self.refresh_services()
                self.update_total()
            except Exception as e:
                utils.show_error("Error", f"Failed to remove service: {e}")
    
    def remove_part(self):
        """Remove selected part"""
        selection = self.parts_tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a part to remove")
            return
        
        item = self.parts_tree.item(selection[0])
        part_id = item['values'][0]
        part_name = item['values'][1]
        
        if utils.ask_yes_no("Confirm", f"Remove part '{part_name}'?"):
            try:
                self.db_manager.delete_spare_part(part_id, self.work_order_id)
                utils.show_info("Success", "Part removed successfully")
                self.refresh_parts()
                self.update_total()
            except Exception as e:
                utils.show_error("Error", f"Failed to remove part: {e}")

class StatusUpdateDialog(BaseDialog):
    """Dialog for updating work order status"""
    
    def __init__(self, parent, current_status):
        self.current_status = current_status
        super().__init__(parent, "Update Status", (400, 200))
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Status
        ttk.Label(main_frame, text="Work Order Status:").grid(row=0, column=0, sticky=W, pady=5)
        self.status_var = tk.StringVar(value=self.current_status)
        status_combo = ttk.Combobox(main_frame, textvariable=self.status_var, 
                                   values=["Open", "In Progress", "Completed"], width=37)
        status_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Payment status
        ttk.Label(main_frame, text="Payment Status:").grid(row=1, column=0, sticky=W, pady=5)
        self.payment_var = tk.StringVar(value="Unpaid")
        payment_combo = ttk.Combobox(main_frame, textvariable=self.payment_var, 
                                    values=["Unpaid", "Paid"], width=37)
        payment_combo.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Update", command=self.on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
    
    def on_ok(self):
        self.result = {
            'status': self.status_var.get(),
            'payment_status': self.payment_var.get()
        }
        self.dialog.destroy()

class InvoiceCreateDialog(BaseDialog):
    """Dialog for creating invoices from work orders"""
    
    def __init__(self, parent, work_orders):
        self.work_orders = work_orders
        super().__init__(parent, "Create Invoice", (800, 600))
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(main_frame, text="Select Work Order to Invoice:", 
                 font=config.FONTS['header']).pack(anchor=W, pady=(0, 10))
        
        # Work orders list
        columns = ('ID', 'License Plate', 'Customer', 'Total Cost')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=12)
        
        self.tree.heading('ID', text='Work Order ID')
        self.tree.heading('License Plate', text='License Plate')
        self.tree.heading('Customer', text='Customer')
        self.tree.heading('Total Cost', text='Total Cost')
        
        self.tree.column('ID', width=100)
        self.tree.column('License Plate', width=120)
        self.tree.column('Customer', width=200)
        self.tree.column('Total Cost', width=120)
        
        # Populate with work orders
        for wo in self.work_orders:
            self.tree.insert('', END, values=(
                wo['id'],
                wo['license_plate'],
                wo['customer_name'],
                utils.format_currency(wo['total_cost'] or 0)
            ))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        
        ttk.Button(button_frame, text="Create Invoice", command=self.on_ok, 
                  bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, 
                  bootstyle=SECONDARY).pack(side=LEFT, padx=5)
    
    def on_ok(self):
        selection = self.tree.selection()
        if not selection:
            utils.show_warning("No Selection", "Please select a work order")
            return
        
        item = self.tree.item(selection[0])
        work_order_id = item['values'][0]
        
        self.result = {'work_order_id': work_order_id}
        self.dialog.destroy()


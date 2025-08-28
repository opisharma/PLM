import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from db_connect import connect_db
import datetime
from decimal import Decimal, InvalidOperation
import csv
import os
from collections import defaultdict

class PersonalExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Life Expenses Manager")
        self.root.geometry("1400x900")
        self.root.state('zoomed')  # Maximize window on Windows
        
        # Color scheme
        self.colors = {
            'primary': '#2E86AB',      # Blue
            'secondary': '#A23B72',    # Pink
            'success': '#F18F01',      # Orange
            'warning': '#C73E1D',      # Red
            'light': '#F5F5F5',       # Light gray
            'dark': '#2C3E50',        # Dark blue
            'white': '#FFFFFF',
            'accent': '#48CAE4'       # Light blue
        }
        
        # Configure root
        self.root.configure(bg=self.colors['light'])
        
        # Initialize database
        self.init_database()
        
        # Setup styles
        self.setup_styles()
        
        # Create main interface
        self.create_main_interface()
        
        # Load initial data
        self.refresh_all_data()
    
    def init_database(self):
        """Initialize database with exact schema using custom db_connect"""
        try:
            # Use shared MySQL connector (db_connect.connect_db)
            self.conn = connect_db()
            if not self.conn:
                raise RuntimeError("Database connection failed")
            # Use dictionary cursor if you prefer: self.conn.cursor(dictionary=True)
            self.cursor = self.conn.cursor()

            # Create table using MySQL-compatible DDL
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    amount DECIMAL(10,2) NOT NULL,
                    category VARCHAR(100) DEFAULT NULL,
                    description TEXT DEFAULT NULL,
                    expense_date DATE DEFAULT (CURRENT_DATE),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Optionally insert sample rows if table empty (safe for dev)
            self.cursor.execute("SELECT COUNT(*) FROM expenses")
            result = self.cursor.fetchone()
            if result and result[0] == 0:
                sample_expenses = [
                    (250.00, 'Food & Dining', 'Weekly groceries from supermarket', '2025-08-25'),
                    (45.99, 'Transportation', 'Bus pass for monthly commute', '2025-08-24'),
                    (120.50, 'Shopping', 'New clothes for office', '2025-08-23'),
                ]
                insert_sql = """
                    INSERT INTO expenses (amount, category, description, expense_date)
                    VALUES (%s, %s, %s, %s)
                """
                for row in sample_expenses:
                    self.cursor.execute(insert_sql, row)

            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")
    
    def setup_styles(self):
        """Setup beautiful custom styles"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure custom styles
        self.style.configure('Title.TLabel', 
                           font=('Segoe UI', 24, 'bold'), 
                           foreground=self.colors['dark'],
                           background=self.colors['light'])
        
        self.style.configure('Heading.TLabel', 
                           font=('Segoe UI', 14, 'bold'), 
                           foreground=self.colors['dark'],
                           background=self.colors['white'])
        
        self.style.configure('Info.TLabel', 
                           font=('Segoe UI', 11), 
                           foreground='#666666',
                           background=self.colors['white'])
        
        self.style.configure('Card.TFrame', 
                           background=self.colors['white'],
                           relief='solid',
                           borderwidth=1)
        
        # Button styles
        self.style.configure('Primary.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           foreground=self.colors['white'],
                           background=self.colors['primary'],
                           focuscolor='none',
                           relief='flat',
                           padding=(20, 10))
        
        self.style.configure('Success.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           foreground=self.colors['white'],
                           background=self.colors['success'],
                           focuscolor='none',
                           relief='flat',
                           padding=(15, 8))
        
        self.style.configure('Warning.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           foreground=self.colors['white'],
                           background=self.colors['warning'],
                           focuscolor='none',
                           relief='flat',
                           padding=(15, 8))
        
        # Tab style
        self.style.configure('Custom.TNotebook.Tab',
                           font=('Segoe UI', 12, 'bold'),
                           padding=(20, 15))
    
    def create_main_interface(self):
        """Create the main beautiful interface"""
        # Header frame
        header_frame = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header_frame, bg=self.colors['primary'])
        header_content.pack(expand=True, fill='both')
        
        title_label = tk.Label(header_content, 
                              text="Personal Life Expenses Manager", 
                              font=('Segoe UI', 20, 'bold'),
                              fg=self.colors['white'],
                              bg=self.colors['primary'])
        title_label.pack(side='left', padx=30, pady=20)
        
        # Current date
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        date_label = tk.Label(header_content, 
                             text=f"{current_date}", 
                             font=('Segoe UI', 12),
                             fg=self.colors['white'],
                             bg=self.colors['primary'])
        date_label.pack(side='right', padx=30, pady=20)
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['light'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True)
        
        # Create all tabs
        self.create_dashboard_tab()
        self.create_add_expense_tab()
        self.create_manage_expenses_tab()
        self.create_reports_tab()
        self.create_settings_tab()
    
    def create_dashboard_tab(self):
        """Create beautiful dashboard tab"""
        dashboard_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Stats cards container
        stats_container = tk.Frame(dashboard_frame, bg=self.colors['light'])
        stats_container.pack(fill='x', padx=20, pady=20)
        
        # Create stats cards
        self.total_card = self.create_stat_card(stats_container, "Total Expenses", "৳0.00", self.colors['primary'], "💰")
        self.total_card.pack(side='left', padx=15, pady=10)
        
        self.monthly_card = self.create_stat_card(stats_container, "This Month", "৳0.00", self.colors['success'], "📊")
        self.monthly_card.pack(side='left', padx=15, pady=10)
        
        self.avg_card = self.create_stat_card(stats_container, "Average Expense", "৳0.00", self.colors['secondary'], "📈")
        self.avg_card.pack(side='left', padx=15, pady=10)
        
        self.count_card = self.create_stat_card(stats_container, "Total Transactions", "0", self.colors['accent'], "🔢")
        self.count_card.pack(side='left', padx=15, pady=10)
        
        # Recent expenses section
        recent_section = tk.Frame(dashboard_frame, bg=self.colors['light'])
        recent_section.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Section title
        recent_title_frame = tk.Frame(recent_section, bg=self.colors['white'], height=50)
        recent_title_frame.pack(fill='x', pady=(0, 10))
        recent_title_frame.pack_propagate(False)
        
        tk.Label(recent_title_frame, text="Recent Transactions", 
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(side='left', padx=20, pady=15)
        
        # Recent expenses treeview
        tree_frame = tk.Frame(recent_section, bg=self.colors['white'])
        tree_frame.pack(fill='both', expand=True)
        
        # Treeview with beautiful styling
        columns = ('Date', 'Category', 'Description', 'Amount')
        self.recent_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        # Configure columns
        self.recent_tree.column('Date', width=120, anchor='center')
        self.recent_tree.column('Category', width=180, anchor='w')
        self.recent_tree.column('Description', width=400, anchor='w')
        self.recent_tree.column('Amount', width=150, anchor='e')
        
        # Configure headings
        for col in columns:
            self.recent_tree.heading(col, text=col, anchor='center')
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.recent_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.recent_tree.xview)
        
        self.recent_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack treeview and scrollbars
        self.recent_tree.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        v_scroll.grid(row=0, column=1, sticky='ns', pady=20)
        h_scroll.grid(row=1, column=0, sticky='ew', padx=20)
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
    
    def create_stat_card(self, parent, title, value, color, icon):
        """Create beautiful stat card"""
        card_frame = tk.Frame(parent, bg=self.colors['white'], relief='solid', bd=1, width=280, height=130)
        card_frame.pack_propagate(False)
        
        # Icon and title
        top_frame = tk.Frame(card_frame, bg=self.colors['white'])
        top_frame.pack(fill='x', padx=20, pady=(15, 5))
        
        icon_label = tk.Label(top_frame, text=icon, font=('Segoe UI', 20), bg=self.colors['white'], fg=color)
        icon_label.pack(side='left')
        
        title_label = tk.Label(top_frame, text=title, font=('Segoe UI', 11, 'bold'), 
                              bg=self.colors['white'], fg='#666666')
        title_label.pack(side='right')
        
        # Value
        value_label = tk.Label(card_frame, text=value, font=('Segoe UI', 18, 'bold'), 
                              bg=self.colors['white'], fg=color)
        value_label.pack(pady=(5, 15))
        
        # Store reference for updates
        card_frame.value_label = value_label
        
        return card_frame
    
    def create_add_expense_tab(self):
        """Create beautiful add expense tab"""
        add_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(add_frame, text="Add Expense")
        
        # Center container
        center_frame = tk.Frame(add_frame, bg=self.colors['light'])
        center_frame.pack(expand=True, fill='both')
        
        # Form card
        form_card = tk.Frame(center_frame, bg=self.colors['white'], relief='solid', bd=1)
        form_card.pack(expand=True, fill='none', padx=100, pady=50, ipadx=50, ipady=30)
        
        # Form title
        title_frame = tk.Frame(form_card, bg=self.colors['white'])
        title_frame.pack(fill='x', pady=(0, 30))
        
        tk.Label(title_frame, text="Add New Expense", 
                font=('Segoe UI', 18, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack()
        
        # Form fields
        fields_frame = tk.Frame(form_card, bg=self.colors['white'])
        fields_frame.pack(fill='both', expand=True, padx=40)
        
        # Amount field
        self.create_form_field(fields_frame, "Amount (৳)", 0)
        self.amount_var = tk.StringVar()
        amount_entry = tk.Entry(fields_frame, textvariable=self.amount_var, 
                               font=('Segoe UI', 12), relief='solid', bd=1, width=30)
        amount_entry.grid(row=0, column=1, sticky='w', padx=(20, 0), pady=15, ipady=8)
        
        # Category field
        self.create_form_field(fields_frame, "Category", 1)
        self.category_var = tk.StringVar()
        categories = [
            'Food & Dining', 'Transportation', 'Shopping', 'Entertainment', 
            'Bills & Utilities', 'Healthcare', 'Personal Care', 'Education',
            'Travel', 'Gifts & Donations', 'Investment', 'Other'
        ]
        category_combo = ttk.Combobox(fields_frame, textvariable=self.category_var, 
                                     values=categories, width=28, font=('Segoe UI', 12))
        category_combo.grid(row=1, column=1, sticky='w', padx=(20, 0), pady=15, ipady=8)
        
        # Description field
        self.create_form_field(fields_frame, "Description", 2)
        self.description_var = tk.StringVar()
        desc_entry = tk.Entry(fields_frame, textvariable=self.description_var, 
                             font=('Segoe UI', 12), relief='solid', bd=1, width=30)
        desc_entry.grid(row=2, column=1, sticky='w', padx=(20, 0), pady=15, ipady=8)
        
        # Date field
        self.create_form_field(fields_frame, "Date", 3)
        self.date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        date_entry = tk.Entry(fields_frame, textvariable=self.date_var, 
                             font=('Segoe UI', 12), relief='solid', bd=1, width=30)
        date_entry.grid(row=3, column=1, sticky='w', padx=(20, 0), pady=15, ipady=8)
        
        # Buttons
        button_frame = tk.Frame(form_card, bg=self.colors['white'])
        button_frame.pack(fill='x', pady=(30, 0), padx=40)
        
        add_btn = tk.Button(button_frame, text="Add Expense", 
                           command=self.add_expense,
                           font=('Segoe UI', 12, 'bold'),
                           bg=self.colors['success'], fg=self.colors['white'],
                           relief='flat', padx=30, pady=10,
                           cursor='hand2')
        add_btn.pack(side='left', padx=(0, 15))
        
        clear_btn = tk.Button(button_frame, text="Clear Form", 
                             command=self.clear_form,
                             font=('Segoe UI', 12, 'bold'),
                             bg='#95A5A6', fg=self.colors['white'],
                             relief='flat', padx=30, pady=10,
                             cursor='hand2')
        clear_btn.pack(side='left')
    
    def create_form_field(self, parent, label_text, row):
        """Create form field label"""
        label = tk.Label(parent, text=label_text, 
                        font=('Segoe UI', 12, 'bold'),
                        fg=self.colors['dark'],
                        bg=self.colors['white'])
        label.grid(row=row, column=0, sticky='w', pady=15)
    
    def create_manage_expenses_tab(self):
        """Create manage expenses tab"""
        manage_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(manage_frame, text="Manage Expenses")
        
        # Filter section
        filter_card = tk.Frame(manage_frame, bg=self.colors['white'], relief='solid', bd=1)
        filter_card.pack(fill='x', padx=20, pady=(20, 10), ipady=15)
        
        tk.Label(filter_card, text="Filters & Search", 
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(pady=(0, 15))
        
        filter_controls = tk.Frame(filter_card, bg=self.colors['white'])
        filter_controls.pack(padx=30)
        
        # Search
        tk.Label(filter_controls, text="Search:", 
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['white']).grid(row=0, column=0, padx=(0, 10), pady=10)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(filter_controls, textvariable=self.search_var, 
                               font=('Segoe UI', 11), width=25, relief='solid', bd=1)
        search_entry.grid(row=0, column=1, padx=(0, 30), pady=10, ipady=5)
        search_entry.bind('<KeyRelease>', lambda e: self.refresh_expenses_list())
        
        # Category filter
        tk.Label(filter_controls, text="Category:", 
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['white']).grid(row=0, column=2, padx=(0, 10), pady=10)
        
        self.filter_category_var = tk.StringVar(value="All Categories")
        categories = ['All Categories', 'Food & Dining', 'Transportation', 'Shopping', 
                     'Entertainment', 'Bills & Utilities', 'Healthcare', 'Personal Care', 
                     'Education', 'Travel', 'Gifts & Donations', 'Investment', 'Other']
        
        category_filter = ttk.Combobox(filter_controls, textvariable=self.filter_category_var, 
                                      values=categories, width=20, font=('Segoe UI', 11))
        category_filter.grid(row=0, column=3, padx=(0, 30), pady=10, ipady=5)
        category_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_expenses_list())
        
        # Date filter
        tk.Label(filter_controls, text="Period:", 
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['white']).grid(row=0, column=4, padx=(0, 10), pady=10)
        
        self.period_var = tk.StringVar(value="All Time")
        periods = ['All Time', 'Today', 'This Week', 'This Month', 'Last 30 Days', 'Last 3 Months']
        
        period_filter = ttk.Combobox(filter_controls, textvariable=self.period_var, 
                                    values=periods, width=15, font=('Segoe UI', 11))
        period_filter.grid(row=0, column=5, pady=10, ipady=5)
        period_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_expenses_list())
        
        # Expenses list section
        list_card = tk.Frame(manage_frame, bg=self.colors['white'], relief='solid', bd=1)
        list_card.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # List header
        list_header = tk.Frame(list_card, bg=self.colors['white'])
        list_header.pack(fill='x', padx=20, pady=(15, 0))
        
        tk.Label(list_header, text="All Expenses", 
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(side='left')
        
        # Action buttons
        action_frame = tk.Frame(list_header, bg=self.colors['white'])
        action_frame.pack(side='right')
        
        edit_btn = tk.Button(action_frame, text="Edit", 
                           command=self.edit_selected_expense,
                           font=('Segoe UI', 10, 'bold'),
                           bg=self.colors['primary'], fg=self.colors['white'],
                           relief='flat', padx=15, pady=5, cursor='hand2')
        edit_btn.pack(side='left', padx=(0, 10))
        
        delete_btn = tk.Button(action_frame, text="Delete", 
                             command=self.delete_selected_expense,
                             font=('Segoe UI', 10, 'bold'),
                             bg=self.colors['warning'], fg=self.colors['white'],
                             relief='flat', padx=15, pady=5, cursor='hand2')
        delete_btn.pack(side='left')
        
        # Expenses treeview
        tree_container = tk.Frame(list_card, bg=self.colors['white'])
        tree_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        columns = ('ID', 'Date', 'Category', 'Description', 'Amount')
        self.expenses_tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.expenses_tree.column('ID', width=60, anchor='center')
        self.expenses_tree.column('Date', width=120, anchor='center')
        self.expenses_tree.column('Category', width=200, anchor='w')
        self.expenses_tree.column('Description', width=350, anchor='w')
        self.expenses_tree.column('Amount', width=150, anchor='e')
        
        # Configure headings
        for col in columns:
            self.expenses_tree.heading(col, text=col, anchor='center')
        
        # Scrollbars for expenses tree
        v_scroll2 = ttk.Scrollbar(tree_container, orient='vertical', command=self.expenses_tree.yview)
        h_scroll2 = ttk.Scrollbar(tree_container, orient='horizontal', command=self.expenses_tree.xview)
        
        self.expenses_tree.configure(yscrollcommand=v_scroll2.set, xscrollcommand=h_scroll2.set)
        
        # Pack expenses tree
        self.expenses_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll2.grid(row=0, column=1, sticky='ns')
        h_scroll2.grid(row=1, column=0, sticky='ew')
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
    
    def create_reports_tab(self):
        """Create reports tab"""
        reports_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(reports_frame, text="Reports")
        
        # Summary statistics card
        stats_card = tk.Frame(reports_frame, bg=self.colors['white'], relief='solid', bd=1)
        stats_card.pack(fill='x', padx=20, pady=20, ipady=20)
        
        tk.Label(stats_card, text="Expense Summary", 
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(pady=(0, 20))
        
        # Create summary text widget
        summary_container = tk.Frame(stats_card, bg=self.colors['white'])
        summary_container.pack(padx=30, pady=(0, 20))
        
        self.summary_text = tk.Text(summary_container, height=15, width=80, 
                                   font=('Segoe UI', 11), 
                                   relief='solid', bd=1,
                                   bg='#F8F9FA')
        self.summary_text.pack(side='left', padx=(0, 10))
        
        # Scrollbar for summary
        summary_scroll = ttk.Scrollbar(summary_container, orient='vertical', command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)
        summary_scroll.pack(side='right', fill='y')
        
        # Export section
        export_card = tk.Frame(reports_frame, bg=self.colors['white'], relief='solid', bd=1)
        export_card.pack(fill='x', padx=20, pady=(0, 20), ipady=20)
        
        tk.Label(export_card, text="Export Options", 
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(pady=(0, 15))
        
        export_buttons = tk.Frame(export_card, bg=self.colors['white'])
        export_buttons.pack()
        
        export_csv_btn = tk.Button(export_buttons, text="Export to CSV", 
                                 command=self.export_to_csv,
                                 font=('Segoe UI', 12, 'bold'),
                                 bg=self.colors['success'], fg=self.colors['white'],
                                 relief='flat', padx=25, pady=10, cursor='hand2')
        export_csv_btn.pack(side='left', padx=15)
        
        backup_btn = tk.Button(export_buttons, text="Create Backup", 
                             command=self.create_backup,
                             font=('Segoe UI', 12, 'bold'),
                             bg=self.colors['primary'], fg=self.colors['white'],
                             relief='flat', padx=25, pady=10, cursor='hand2')
        backup_btn.pack(side='left', padx=15)
        
        refresh_report_btn = tk.Button(export_buttons, text="Refresh Report", 
                                     command=self.generate_summary_report,
                                     font=('Segoe UI', 12, 'bold'),
                                     bg=self.colors['secondary'], fg=self.colors['white'],
                                     relief='flat', padx=25, pady=10, cursor='hand2')
        refresh_report_btn.pack(side='left', padx=15)
    
    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = tk.Frame(self.notebook, bg=self.colors['light'])
        self.notebook.add(settings_frame, text="Settings")
        
        # Database section
        db_card = tk.Frame(settings_frame, bg=self.colors['white'], relief='solid', bd=1)
        db_card.pack(fill='x', padx=20, pady=20, ipady=20)
        
        tk.Label(db_card, text="Database Management", 
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(pady=(0, 15))
        
        db_buttons = tk.Frame(db_card, bg=self.colors['white'])
        db_buttons.pack()
        
        import_btn = tk.Button(db_buttons, text="Import from CSV", 
                             command=self.import_from_csv,
                             font=('Segoe UI', 12, 'bold'),
                             bg=self.colors['primary'], fg=self.colors['white'],
                             relief='flat', padx=25, pady=10, cursor='hand2')
        import_btn.pack(side='left', padx=15)
        
        clear_db_btn = tk.Button(db_buttons, text="Clear All Data", 
                                command=self.clear_all_data,
                                font=('Segoe UI', 12, 'bold'),
                                bg=self.colors['warning'], fg=self.colors['white'],
                                relief='flat', padx=25, pady=10, cursor='hand2')
        clear_db_btn.pack(side='left', padx=15)
        
        # About section
        about_card = tk.Frame(settings_frame, bg=self.colors['white'], relief='solid', bd=1)
        about_card.pack(fill='x', padx=20, pady=(0, 20), ipady=30)
        
        tk.Label(about_card, text="About", 
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(pady=(0, 15))
        
        about_text = """
        Personal Life Expenses Manager v1.0
        
        Features:
        • Beautiful and intuitive user interface
        • Complete expense tracking and management
        • Advanced filtering and search capabilities
        • Detailed reports and analytics
        • CSV import/export functionality
        • Database backup and restore
        
        Built with Python & Tkinter
        Custom Database Integration
        Modern UI Design
        
        Created for personal expense management
        """
        
        tk.Label(about_card, text=about_text, 
                font=('Segoe UI', 11),
                fg='#666666',
                bg=self.colors['white'],
                justify='left').pack()
    
    # === Database Operations ===
    
    def add_expense(self):
        """Add new expense to database"""
        try:
            # Get form data
            amount_str = self.amount_var.get().strip()
            category = self.category_var.get().strip()
            description = self.description_var.get().strip()
            expense_date = self.date_var.get().strip()
            
            # Validation
            if not all([amount_str, category, description, expense_date]):
                messagebox.showerror("Error", "Please fill in all fields!")
                return
            
            # Convert and validate amount
            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid positive amount!")
                return
            
            # Validate date format
            try:
                datetime.datetime.strptime(expense_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error", "Please enter date in YYYY-MM-DD format!")
                return
            
            # Insert into database using MySQL placeholders
            insert_sql = """
                INSERT INTO expenses (amount, category, description, expense_date)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(insert_sql, (amount, category, description, expense_date))
            
            self.conn.commit()
            
            # Success message
            messagebox.showinfo("Success", f"Expense of ৳{amount:.2f} added successfully!")
            
            # Clear form and refresh
            self.clear_form()
            self.refresh_all_data()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add expense: {e}")
    
    def clear_form(self):
        """Clear the add expense form"""
        self.amount_var.set("")
        self.category_var.set("")
        self.description_var.set("")
        self.date_var.set(datetime.date.today().strftime('%Y-%m-%d'))
    
    def refresh_all_data(self):
        """Refresh all data displays"""
        self.update_dashboard_stats()
        self.refresh_recent_expenses()
        self.refresh_expenses_list()
        self.generate_summary_report()
    
    def update_dashboard_stats(self):
        """Update dashboard statistics cards"""
        try:
            # Get total statistics
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_count,
                    COALESCE(SUM(amount), 0) as total_amount,
                    COALESCE(AVG(amount), 0) as avg_amount
                FROM expenses
            """)
            
            result = self.cursor.fetchone()
            if result:
                total_count, total_amount, avg_amount = result
            else:
                total_count, total_amount, avg_amount = 0, 0, 0
            
            # Get this month's total
            # MySQL: compare with first day of current month
            month_start = datetime.date.today().replace(day=1).strftime('%Y-%m-%d')
            self.cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE expense_date >= %s
            """, (month_start,))
            
            result = self.cursor.fetchone()
            monthly_amount = result[0] if result else 0
            
            # Update cards
            self.total_card.value_label.config(text=f"৳{total_amount:,.2f}")
            self.monthly_card.value_label.config(text=f"৳{monthly_amount:,.2f}")
            self.avg_card.value_label.config(text=f"৳{avg_amount:,.2f}")
            self.count_card.value_label.config(text=f"{total_count:,}")
            
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
    
    def refresh_recent_expenses(self):
        """Refresh recent expenses in dashboard"""
        try:
            # Clear existing items
            for item in self.recent_tree.get_children():
                self.recent_tree.delete(item)
            
            # Get recent expenses
            self.cursor.execute("""
                SELECT expense_date, category, description, amount
                FROM expenses
                ORDER BY created_at DESC, id DESC
                LIMIT 10
            """)
            
            rows = self.cursor.fetchall()
            for row in rows:
                date_str = row[0]
                category = row[1] or "No Category"
                description = row[2] or "No Description"
                # Truncate long descriptions
                if len(description) > 40:
                    description = description[:37] + "..."
                amount_str = f"৳{row[3]:,.2f}"
                
                self.recent_tree.insert('', 'end', values=(date_str, category, description, amount_str))
                
        except Exception as e:
            print(f"Error refreshing recent expenses: {e}")
    
    def refresh_expenses_list(self):
        """Refresh expenses list with filters applied"""
        try:
            # Clear existing items
            for item in self.expenses_tree.get_children():
                self.expenses_tree.delete(item)
            
            # Build query with filters
            query = "SELECT id, expense_date, category, description, amount FROM expenses WHERE 1=1"
            params = []
            
            # Apply search filter
            search_term = self.search_var.get().strip()
            if search_term:
                query += " AND (description LIKE %s OR category LIKE %s)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])
            
            # Apply category filter
            category_filter = self.filter_category_var.get()
            if category_filter != "All Categories":
                query += " AND category = %s"
                params.append(category_filter)
            
            # Apply date period filter
            period = self.period_var.get()
            if period != "All Time":
                today = datetime.date.today()
                
                if period == "Today":
                    query += " AND expense_date = %s"
                    params.append(today.strftime('%Y-%m-%d'))
                elif period == "This Week":
                    week_start = today - datetime.timedelta(days=today.weekday())
                    query += " AND expense_date >= %s"
                    params.append(week_start.strftime('%Y-%m-%d'))
                elif period == "This Month":
                    month_start = today.replace(day=1)
                    query += " AND expense_date >= %s"
                    params.append(month_start.strftime('%Y-%m-%d'))
                elif period == "Last 30 Days":
                    thirty_days_ago = today - datetime.timedelta(days=30)
                    query += " AND expense_date >= %s"
                    params.append(thirty_days_ago.strftime('%Y-%m-%d'))
                elif period == "Last 3 Months":
                    three_months_ago = today - datetime.timedelta(days=90)
                    query += " AND expense_date >= %s"
                    params.append(three_months_ago.strftime('%Y-%m-%d'))
            
            query += " ORDER BY expense_date DESC, created_at DESC"
            
            # Execute query
            self.cursor.execute(query, tuple(params))
            
            # Populate treeview
            rows = self.cursor.fetchall()
            for row in rows:
                expense_id, date_str, category, description, amount = row
                category = category or "No Category"
                description = description or "No Description"
                
                # Truncate long descriptions for display
                if len(description) > 35:
                    description = description[:32] + "..."
                
                amount_str = f"৳{amount:,.2f}"
                
                self.expenses_tree.insert('', 'end', values=(
                    expense_id, date_str, category, description, amount_str
                ))
                
        except Exception as e:
            print(f"Error refreshing expenses list: {e}")
    
    def edit_selected_expense(self):
        """Edit the selected expense"""
        selected = self.expenses_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to edit!")
            return
        
        # Get selected item data
        item = self.expenses_tree.item(selected[0])
        expense_id = item['values'][0]
        
        # Get full expense data from database
        try:
            self.cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
            expense_data = self.cursor.fetchone()
            
            if expense_data:
                self.open_edit_dialog(expense_data)
            else:
                messagebox.showerror("Error", "Expense not found in database!")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to retrieve expense: {e}")
    
    def open_edit_dialog(self, expense_data):
        """Open edit expense dialog"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Expense")
        edit_window.geometry("500x400")
        edit_window.configure(bg=self.colors['light'])
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Center the window
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = tk.Frame(edit_window, bg=self.colors['white'], relief='solid', bd=1)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_frame, text="Edit Expense", 
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(pady=(20, 30))
        
        # Form fields
        fields_frame = tk.Frame(main_frame, bg=self.colors['white'])
        fields_frame.pack(padx=40)
        
        # Amount
        tk.Label(fields_frame, text="Amount (৳):", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).grid(row=0, column=0, sticky='w', pady=15)
        
        amount_var = tk.StringVar(value=str(expense_data[1]))
        amount_entry = tk.Entry(fields_frame, textvariable=amount_var, 
                               font=('Segoe UI', 12), width=25, relief='solid', bd=1)
        amount_entry.grid(row=0, column=1, padx=(20, 0), pady=15, ipady=5)
        
        # Category
        tk.Label(fields_frame, text="Category:", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).grid(row=1, column=0, sticky='w', pady=15)
        
        category_var = tk.StringVar(value=expense_data[2] or "")
        categories = [
            'Food & Dining', 'Transportation', 'Shopping', 'Entertainment', 
            'Bills & Utilities', 'Healthcare', 'Personal Care', 'Education',
            'Travel', 'Gifts & Donations', 'Investment', 'Other'
        ]
        category_combo = ttk.Combobox(fields_frame, textvariable=category_var, 
                                     values=categories, width=23, font=('Segoe UI', 12))
        category_combo.grid(row=1, column=1, padx=(20, 0), pady=15, ipady=5)
        
        # Description
        tk.Label(fields_frame, text="Description:", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).grid(row=2, column=0, sticky='w', pady=15)
        
        description_var = tk.StringVar(value=expense_data[3] or "")
        desc_entry = tk.Entry(fields_frame, textvariable=description_var, 
                             font=('Segoe UI', 12), width=25, relief='solid', bd=1)
        desc_entry.grid(row=2, column=1, padx=(20, 0), pady=15, ipady=5)
        
        # Date
        tk.Label(fields_frame, text="Date:", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['dark'],
                bg=self.colors['white']).grid(row=3, column=0, sticky='w', pady=15)
        
        date_var = tk.StringVar(value=expense_data[4] or datetime.date.today().strftime('%Y-%m-%d'))
        date_entry = tk.Entry(fields_frame, textvariable=date_var, 
                             font=('Segoe UI', 12), width=25, relief='solid', bd=1)
        date_entry.grid(row=3, column=1, padx=(20, 0), pady=15, ipady=5)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['white'])
        button_frame.pack(pady=(30, 20))
        
        def save_changes():
            try:
                # Validate inputs
                amount_str = amount_var.get().strip()
                category = category_var.get().strip()
                description = description_var.get().strip()
                expense_date = date_var.get().strip()
                
                if not all([amount_str, category, description, expense_date]):
                    messagebox.showerror("Error", "Please fill in all fields!")
                    return
                
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                
                # Validate date
                datetime.datetime.strptime(expense_date, '%Y-%m-%d')
                
                # Update database
                self.cursor.execute("""
                    UPDATE expenses
                    SET amount=%s, category=%s, description=%s, expense_date=%s
                    WHERE id=%s
                """, (amount, category, description, expense_date, expense_data[0]))
                
                self.conn.commit()
                
                messagebox.showinfo("Success", "Expense updated successfully!")
                edit_window.destroy()
                self.refresh_all_data()
                
            except ValueError as e:
                if "time data" in str(e):
                    messagebox.showerror("Error", "Please enter date in YYYY-MM-DD format!")
                else:
                    messagebox.showerror("Error", "Please enter a valid positive amount!")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update expense: {e}")
        
        save_btn = tk.Button(button_frame, text="Save Changes", 
                           command=save_changes,
                           font=('Segoe UI', 12, 'bold'),
                           bg=self.colors['success'], fg=self.colors['white'],
                           relief='flat', padx=20, pady=8, cursor='hand2')
        save_btn.pack(side='left', padx=(0, 15))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                             command=edit_window.destroy,
                             font=('Segoe UI', 12, 'bold'),
                             bg='#95A5A6', fg=self.colors['white'],
                             relief='flat', padx=20, pady=8, cursor='hand2')
        cancel_btn.pack(side='left')
    
    def delete_selected_expense(self):
        """Delete the selected expense"""
        selected = self.expenses_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to delete!")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", 
                                  "Are you sure you want to delete this expense?\n\nThis action cannot be undone."):
            return
        
        # Get selected item data
        item = self.expenses_tree.item(selected[0])
        expense_id = item['values'][0]
        
        try:
            # Delete from database
            self.cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
            self.conn.commit()
            
            messagebox.showinfo("Success", "Expense deleted successfully!")
            self.refresh_all_data()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete expense: {e}")
    
    def generate_summary_report(self):
        """Generate and display summary report"""
        try:
            self.summary_text.delete(1.0, tk.END)
            
            report = "PERSONAL EXPENSE SUMMARY REPORT\n"
            report += "=" * 50 + "\n\n"
            
            # Overall statistics
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as total_count,
                    COALESCE(SUM(amount), 0) as total_amount,
                    COALESCE(AVG(amount), 0) as avg_amount,
                    COALESCE(MIN(amount), 0) as min_amount,
                    COALESCE(MAX(amount), 0) as max_amount
                FROM expenses
            ''')
            
            result = self.cursor.fetchone()
            if result:
                total_count, total_amount, avg_amount, min_amount, max_amount = result
            else:
                total_count, total_amount, avg_amount, min_amount, max_amount = 0, 0, 0, 0, 0
            
            report += f"OVERALL STATISTICS:\n"
            report += f"   Total Expenses: {total_count:,} transactions\n"
            report += f"   Total Amount: ৳{total_amount:,.2f}\n"
            report += f"   Average Expense: ৳{avg_amount:,.2f}\n"
            report += f"   Minimum Expense: ৳{min_amount:,.2f}\n"
            report += f"   Maximum Expense: ৳{max_amount:,.2f}\n\n"
            
            # Monthly breakdown
            report += f"MONTHLY BREAKDOWN:\n"
            self.cursor.execute('''
                SELECT 
                    strftime('%Y-%m', expense_date) as month,
                    COUNT(*) as count,
                    SUM(amount) as total
                FROM expenses 
                GROUP BY month 
                ORDER BY month DESC
                LIMIT 6
            ''')
            
            monthly_data = self.cursor.fetchall()
            for month, count, total in monthly_data:
                month_name = datetime.datetime.strptime(month, '%Y-%m').strftime('%B %Y')
                report += f"   {month_name}: {count} transactions, ৳{total:,.2f}\n"
            
            # Category breakdown
            report += f"\nCATEGORY BREAKDOWN:\n"
            self.cursor.execute('''
                SELECT 
                    COALESCE(category, 'Uncategorized') as cat,
                    COUNT(*) as count,
                    SUM(amount) as total,
                    ROUND(AVG(amount), 2) as avg
                FROM expenses 
                GROUP BY category 
                ORDER BY total DESC
            ''')
            
            category_data = self.cursor.fetchall()
            for category, count, total, avg in category_data:
                percentage = (total / total_amount * 100) if total_amount > 0 else 0
                report += f"   {category}: {count} transactions, ৳{total:,.2f} ({percentage:.1f}%), Avg: ৳{avg:,.2f}\n"
            
            # Recent expensive transactions
            report += f"\nTOP 5 HIGHEST EXPENSES:\n"
            self.cursor.execute('''
                SELECT expense_date, category, description, amount
                FROM expenses 
                ORDER BY amount DESC
                LIMIT 5
            ''')
            
            top_expenses = self.cursor.fetchall()
            for date, category, description, amount in top_expenses:
                category = category or "No Category"
                description = description or "No Description"
                if len(description) > 30:
                    description = description[:27] + "..."
                report += f"   {date} | {category} | {description} | ৳{amount:,.2f}\n"
            
            report += f"\nReport generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += "=" * 50;
            
            self.summary_text.insert(1.0, report)
            
        except Exception as e:
            self.summary_text.insert(1.0, f"Error generating report: {e}")
    
    def export_to_csv(self):
        """Export expenses to CSV file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Expenses to CSV",
                initialname=f"personal_expenses_{datetime.date.today().strftime('%Y%m%d')}.csv"
            )
            
            if filename:
                self.cursor.execute("""
                    SELECT id, amount, category, description, expense_date, created_at
                    FROM expenses
                    ORDER BY expense_date DESC, created_at DESC
                """)
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['ID', 'Amount', 'Category', 'Description', 'Expense Date', 'Created At'])
                    writer.writerows(self.cursor.fetchall())
                
                messagebox.showinfo("Success", f"Expenses exported successfully!\n\nFile saved: {filename}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export expenses: {e}")
    
    def import_from_csv(self):
        """Import expenses from CSV file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Import Expenses from CSV"
            )
            
            if filename:
                if not messagebox.askyesno("Confirm Import", 
                                         "This will import new expenses from the CSV file.\n\nContinue?"):
                    return
                
                imported_count = 0
                errors = []
                
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    # Skip header row if it exists
                    first_row = next(reader, None)
                    if first_row and first_row[0].lower() in ['id', 'amount']:
                        # This is likely a header row, skip it
                        pass
                    else:
                        # This is data, process it
                        csvfile.seek(0)
                        reader = csv.reader(csvfile)
                    
                    for row_num, row in enumerate(reader, start=1):
                        try:
                            if len(row) >= 4:
                                # Expected format: amount, category, description, expense_date
                                amount = float(row[0])
                                category = row[1].strip()
                                description = row[2].strip()
                                expense_date = row[3].strip()
                                
                                # Validate date format
                                datetime.datetime.strptime(expense_date, '%Y-%m-%d')
                                
                                self.cursor.execute('''
                                    INSERT INTO expenses (amount, category, description, expense_date)
                                    VALUES (?, ?, ?, ?)
                                ''', (amount, category, description, expense_date))
                                
                                imported_count += 1
                            else:
                                errors.append(f"Row {row_num}: Insufficient data (need amount, category, description, date)")
                        
                        except (ValueError, Exception) as e:
                            errors.append(f"Row {row_num}: {str(e)}")
                
                self.conn.commit()
                
                # Show results
                message = f"Successfully imported {imported_count} expenses!"
                if errors:
                    message += f"\n\nErrors encountered:\n" + "\n".join(errors[:3])
                    if len(errors) > 3:
                        message += f"\n... and {len(errors) - 3} more errors"
                
                messagebox.showinfo("Import Results", message)
                self.refresh_all_data()
        
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import expenses: {e}")
    
    def create_backup(self):
        """Create database backup"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Create Database Backup",
                initialname=f"personal_expenses_backup_{datetime.date.today().strftime('%Y%m%d')}.csv"
            )
            
            if filename:
                self.cursor.execute('''
                    SELECT id, amount, category, description, expense_date, created_at
                    FROM expenses 
                    ORDER BY expense_date DESC, created_at DESC
                ''')
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['ID', 'Amount', 'Category', 'Description', 'Expense Date', 'Created At'])
                    writer.writerows(self.cursor.fetchall())
                
                messagebox.showinfo("Success", f"Database backup created successfully!\n\nFile saved: {filename}")
        
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup: {e}")
    
    def clear_all_data(self):
        """Clear all expense data"""
        if messagebox.askyesno("Warning", 
                             "This will delete ALL expense data permanently!\n\nAre you absolutely sure?\n\nThis action cannot be undone."):
            if messagebox.askyesno("Final Confirmation", 
                                 "Last chance! Delete all expense data?"):
                try:
                    self.cursor.execute('DELETE FROM expenses')
                    self.conn.commit()
                    
                    messagebox.showinfo("Success", "All expense data has been cleared!")
                    self.refresh_all_data()
                    
                except Exception as e:
                    messagebox.showerror("Database Error", f"Failed to clear data: {e}")
    
    def __del__(self):
        """Cleanup database connection"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass

def main():
    """Main function to run the application"""
    try:
        root = tk.Tk()
        
        # Set application icon if available
        try:
            if os.path.exists('expense_icon.ico'):
                root.iconbitmap('expense_icon.ico')
        except:
            pass
        
        # Create the application
        app = PersonalExpenseTracker(root)
        
        # Handle window closing
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to exit Personal Life Expenses Manager?"):
                try:
                    app.conn.close()
                except:
                    pass
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")

if __name__ == "__main__":
    main()

    
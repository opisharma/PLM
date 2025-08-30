import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import mysql.connector
import db_connect

# MySQL Database connection and management
class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect_db()

    def connect_db(self) -> bool:
        """Connect to MySQL using db_connect.connect_db()"""
        try:
            conn = db_connect.connect_db()
            if conn:
                self.connection = conn
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ connect_db error: {e}")
            messagebox.showerror("Database Error", f"Failed to connect: {e}")
            return False

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute SQL. Returns fetched rows if fetch=True, else returns lastrowid (or True on success)."""
        if not self.connection:
            if not self.connect_db():
                return [] if fetch else None

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            if fetch:
                rows = cursor.fetchall()
                cursor.close()
                return rows
            else:
                self.connection.commit()
                last_id = getattr(cursor, "lastrowid", None)
                cursor.close()
                return last_id if last_id else True
        except mysql.connector.Error as err:
            print(f"❌ Database error: {err}")
            messagebox.showerror("Database Error", f"Database operation failed:\n{err}")
            return [] if fetch else None

    def close_connection(self):
        """Close database connection"""
        try:
            if self.connection:
                try:
                    is_connected = getattr(self.connection, "is_connected", lambda: True)()
                except Exception:
                    is_connected = True
                if is_connected:
                    self.connection.close()
                    print("Database connection closed")
        except Exception:
            pass


class GoalsManager:
    def __init__(self):
        self.db = DatabaseManager()
        
    def create_goal(self, user_id: int, title: str, description: str = None, 
                   goal_type: str = "general", target_value: float = None, 
                   deadline: str = None, priority: str = "Medium") -> int:
        """Create a new goal"""
        try:
            query = """
            INSERT INTO goals (user_id, title, description, goal_type, target_value, deadline, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = (user_id, title, description, goal_type, target_value, deadline, priority)
            
            goal_id = self.db.execute_query(query, params)
            
            if goal_id:
                return goal_id
            else:
                messagebox.showerror("Error", "Failed to create goal in database")
                return None
                
        except Exception as err:
            messagebox.showerror("Error", f"Failed to create goal: {err}")
            return None
    
    def get_goals(self, user_id: int, status: str = None) -> List[Dict]:
        """Get user goals"""
        try:
            query = "SELECT * FROM goals WHERE user_id = %s"
            params = [user_id]
            
            if status:
                query += " AND status = %s"
                params.append(status)
                
            query += " ORDER BY created_at DESC"
            
            goals = self.db.execute_query(query, params, fetch=True)
            return goals or []
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to get goals: {err}")
            return []
    
    def get_goal_by_id(self, goal_id: int, user_id: int) -> Dict:
        """Get specific goal"""
        try:
            query = "SELECT * FROM goals WHERE id = %s AND user_id = %s"
            params = (goal_id, user_id)
            
            goals = self.db.execute_query(query, params, fetch=True)
            
            if goals:
                return goals[0]
            return None
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to get goal: {err}")
            return None
    
    def update_goal_progress(self, goal_id: int, user_id: int, current_value: float, 
                           notes: str = None) -> bool:
        """Update goal progress"""
        try:
            # Get goal to calculate progress
            goal = self.get_goal_by_id(goal_id, user_id)
            if not goal:
                return False
            
            target_value = goal['target_value']
            if target_value and target_value > 0:
                progress_percentage = min(100, int((current_value / target_value) * 100))
            else:
                progress_percentage = 0
            
            # Update goal progress
            update_query = """
            UPDATE goals 
            SET current_value = %s, progress_percentage = %s, updated_at = NOW()
            WHERE id = %s AND user_id = %s
            """
            update_params = (current_value, progress_percentage, goal_id, user_id)
            
            result = self.db.execute_query(update_query, update_params)
            
            # Add progress record
            progress_query = """
            INSERT INTO progress (goal_id, user_id, progress_percentage, notes)
            VALUES (%s, %s, %s, %s)
            """
            progress_params = (goal_id, user_id, progress_percentage, notes)
            
            self.db.execute_query(progress_query, progress_params)
            
            # Auto-complete if 100%
            if progress_percentage >= 100:
                self.complete_goal(goal_id, user_id)
            
            return True
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to update progress: {err}")
            return False
    
    def complete_goal(self, goal_id: int, user_id: int) -> bool:
        """Complete a goal"""
        try:
            query = """
            UPDATE goals 
            SET status = 'Completed', progress_percentage = 100, updated_at = NOW()
            WHERE id = %s AND user_id = %s
            """
            params = (goal_id, user_id)
            
            result = self.db.execute_query(query, params)
            return result is not None
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to complete goal: {err}")
            return False
    
    def delete_goal(self, goal_id: int, user_id: int) -> bool:
        """Delete a goal"""
        try:
            # Delete goal (progress records will be deleted automatically due to CASCADE)
            query = "DELETE FROM goals WHERE id = %s AND user_id = %s"
            params = (goal_id, user_id)
            
            result = self.db.execute_query(query, params)
            return result is not None
                
        except Exception as err:
            messagebox.showerror("Error", f"Failed to delete goal: {err}")
            return False
    
    def get_user_goal_stats(self, user_id: int) -> Dict:
        """Get user goal statistics"""
        try:
            # Get basic counts
            stats_query = """
            SELECT 
                COUNT(*) as total_goals,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_goals,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_goals,
                AVG(CASE WHEN status = 'Active' THEN progress_percentage ELSE NULL END) as avg_progress
            FROM goals 
            WHERE user_id = %s
            """
            
            stats_result = self.db.execute_query(stats_query, (user_id,), fetch=True)
            
            if not stats_result:
                return {}
            
            stats = stats_result[0]
            
            total_goals = stats['total_goals'] or 0
            completed_goals = stats['completed_goals'] or 0
            active_goals = stats['active_goals'] or 0
            avg_progress = stats['avg_progress'] or 0
            
            completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
            
            return {
                'total_goals': total_goals,
                'completed_goals': completed_goals,
                'active_goals': active_goals,
                'completion_rate': completion_rate,
                'average_progress': round(float(avg_progress), 2)
            }
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to get statistics: {err}")
            return {}


class ModernGoalsManagerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Goals Management System - Professional Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f8f9fa')
        self.root.state('zoomed')  # Maximize window
        
        # Business color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'light': '#ecf0f1',
            'dark': '#34495e',
            'white': '#ffffff',
            'background': '#f8f9fa',
            'sidebar': '#2c3e50',
            'card': '#ffffff'
        }
        
        # Database manager
        self.gm = GoalsManager()
        # ensure attributes exist so other methods can safely reference them
        self.table_frame = None
        self.table = None
        self.main_container = None
        
        # Check database connection
        if not self.gm.db.connection:
            messagebox.showerror("Database Error", 
                               "Could not connect to database. Please check your MySQL server and database configuration.")
            self.root.destroy()
            return
        
        # Current user (in real app, this would come from login)
        self.current_user_id = 1
        
        # Configure styles
        self.setup_modern_styles()
        
        # Create modern GUI
        self.create_modern_layout()
        
        # Add welcome banner for first-time users
        self.create_welcome_banner()
        
        # Load initial data
        self.refresh_goals_list()
        
        # Set window icon and properties
        self.root.iconname("Goals Manager")
        self.root.minsize(1200, 700)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Close database connection
            if self.gm and self.gm.db:
                self.gm.db.close_connection()
        except:
            pass
        finally:
            self.root.destroy()
    
    def setup_modern_styles(self):
        """Setup modern business styles"""
        style = ttk.Style()
        
        # Use a modern theme
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # Custom styles for modern look
        style.configure('Modern.TFrame', background=self.colors['card'])
        style.configure('Sidebar.TFrame', background=self.colors['sidebar'])
        
        # Title styles
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 24, 'bold'), 
                       foreground=self.colors['primary'],
                       background=self.colors['background'])
        
        style.configure('SidebarTitle.TLabel', 
                       font=('Segoe UI', 16, 'bold'), 
                       foreground=self.colors['white'],
                       background=self.colors['sidebar'])
        
        style.configure('Heading.TLabel', 
                       font=('Segoe UI', 12, 'bold'), 
                       foreground=self.colors['dark'])
        
        style.configure('Subheading.TLabel', 
                       font=('Segoe UI', 10), 
                       foreground=self.colors['dark'])
        
        # Button styles
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(20, 10))
        
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 10),
                       padding=(15, 8))
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 10),
                       padding=(15, 8))
        
        style.configure('Danger.TButton',
                       font=('Segoe UI', 10),
                       padding=(15, 8))
        
        # Stats styles
        style.configure('Stats.TLabel', 
                       font=('Segoe UI', 14, 'bold'), 
                       foreground=self.colors['primary'])
        
        style.configure('StatsValue.TLabel', 
                       font=('Segoe UI', 18, 'bold'), 
                       foreground=self.colors['secondary'])
        
        # Card styles
        style.configure('Card.TFrame',
                       background=self.colors['card'],
                       relief='solid',
                       borderwidth=1)
    
    def create_modern_layout(self):
        """Create modern business layout"""
        # Main container with padding
        self.main_container = tk.Frame(self.root, bg=self.colors['background'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.create_header()
        
        # Content area with sidebar and main content
        self.content_frame = tk.Frame(self.main_container, bg=self.colors['background'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Sidebar
        self.create_sidebar()
        
        # Main content area
        self.create_main_content()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.priority_filter.pack(fill=tk.X, pady=(5, 0))
    
    def create_sidebar_stats(self, parent):
        """Create compact stats cards for sidebar"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            return
        
        # Stats container
        stats_container = tk.Frame(parent, bg=self.colors['sidebar'])
        stats_container.pack(fill=tk.X, pady=(0, 10))
        
        # Individual stat cards
        stat_items = [
            ("Total Goals", stats['total_goals'], self.colors['secondary']),
            ("Completed", stats['completed_goals'], self.colors['success']),
            ("Active", stats['active_goals'], self.colors['warning']),
            ("Success Rate", f"{stats['completion_rate']:.0f}%", self.colors['success'])
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = tk.Frame(stats_container, bg=color, height=60)
            card.pack(fill=tk.X, pady=2)
            card.pack_propagate(False)
            
            # Value
            val_label = tk.Label(card, text=str(value), font=('Segoe UI', 16, 'bold'), 
                               fg=self.colors['white'], bg=color)
            val_label.place(relx=0.5, rely=0.3, anchor='center')
            
            # Label
            lbl_label = tk.Label(card, text=label, font=('Segoe UI', 9), 
                               fg=self.colors['white'], bg=color)
            lbl_label.place(relx=0.5, rely=0.7, anchor='center')
    
    def create_main_content(self):
        """Create main content area and ensure main_container/table exist."""
        try:
            # create or reuse a main content container for the table and details
            if not getattr(self, "main_container", None):
                self.main_container = tk.Frame(self.root, bg=self.colors['background'])
                self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
            
            # ensure the table is created
            self.create_modern_table(self.main_container)
        except Exception as e:
            print("create_main_content error:", e)

    def create_modern_table(self, parent):
        """Create or return the main table frame and Treeview. Safe to call multiple times."""
        try:
            # If already created and still exists, return current frame
            if getattr(self, "table_frame", None) and self.table_frame.winfo_exists():
                return self.table_frame

            # create container frame for table
            self.table_frame = tk.Frame(parent, bg=self.colors['card'])
            self.table_frame.pack(fill=tk.BOTH, expand=True)

            # create Treeview if not exists
            if not getattr(self, "table", None):
                cols = ("id", "title", "status", "progress", "deadline")
                self.table = ttk.Treeview(self.table_frame, columns=cols, show="headings")
                for c in cols:
                    self.table.heading(c, text=c.capitalize())
                    self.table.column(c, width=120, anchor="w")
                self.table.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

            return self.table_frame
        except Exception as e:
            print("create_modern_table error:", e)
            return None

    def refresh_goals_list(self, search_term=""):
        """Refreshes the table safely using self.table (Treeview)."""
        try:
            # Ensure UI container and table exist
            parent = getattr(self, "main_container", None) or self.root
            self.create_modern_table(parent)

            tree = getattr(self, "table", None)
            if tree is None:
                return

            # clear existing rows
            for row in tree.get_children():
                tree.delete(row)

            # load goals
            goals = self.gm.get_goals(self.current_user_id, None) or []
            for g in goals:
                tree.insert("", "end", values=(
                    g.get("id"),
                    g.get("title"),
                    g.get("status"),
                    g.get("progress_percentage", 0),
                    g.get("deadline") or ""
                ))
        except Exception as e:
            print("refresh_goals_list error:", e)
    
    def create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['background'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Company logo area (placeholder)
        logo_frame = tk.Frame(header_frame, bg=self.colors['primary'], width=60, height=60)
        logo_frame.place(x=0, y=10)
        
        logo_label = tk.Label(logo_frame, text="GM", font=('Segoe UI', 16, 'bold'), 
                            fg=self.colors['white'], bg=self.colors['primary'])
        logo_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = ttk.Label(header_frame, text="Goals Management System", style='Title.TLabel')
        title_label.place(x=80, y=15)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Professional Edition - MySQL Powered", 
                                 font=('Segoe UI', 11), foreground=self.colors['dark'])
        subtitle_label.place(x=80, y=45)
        
        # User info (top right)
        user_frame = tk.Frame(header_frame, bg=self.colors['background'])
        user_frame.place(relx=1.0, rely=0.5, anchor='e')
        
        user_label = ttk.Label(user_frame, text="👤 Personal User", 
                             font=('Segoe UI', 10), foreground=self.colors['dark'])
        user_label.pack()
        
        # Separator line
        separator = tk.Frame(header_frame, bg=self.colors['secondary'], height=2)
        separator.place(x=0, rely=1.0, relwidth=1.0, anchor='sw')
    
    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        # Sidebar container
        sidebar_container = tk.Frame(self.content_frame, bg=self.colors['sidebar'], width=280)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar_container.pack_propagate(False)
        
        # Sidebar content with padding
        sidebar_frame = tk.Frame(sidebar_container, bg=self.colors['sidebar'])
        sidebar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sidebar title
        ttk.Label(sidebar_frame, text="📊 Dashboard", style='SidebarTitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Quick stats cards in sidebar
        self.create_sidebar_stats(sidebar_frame)
        
        # Action buttons
        ttk.Label(sidebar_frame, text="⚡ Quick Actions", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Modern button list
        buttons_config = [
            ("➕ Create New Goal", self.create_goal_dialog, 'Primary.TButton'),
            ("📈 Update Progress", self.update_progress_dialog, 'Secondary.TButton'),
            ("✅ Mark Complete", self.complete_goal_dialog, 'Success.TButton'),
            ("🔄 Refresh Data", self.refresh_goals_list, 'Secondary.TButton'),
            ("📊 View Analytics", self.show_detailed_statistics, 'Secondary.TButton'),
            ("🗑️ Delete Goal", self.delete_goal_dialog, 'Danger.TButton'),
        ]
        
        for text, command, style in buttons_config:
            btn_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
            btn_frame.pack(fill=tk.X, pady=3)
            
            btn = ttk.Button(btn_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X)
        
        # Filter section
        ttk.Label(sidebar_frame, text="🔍 Filters", style='SidebarTitle.TLabel').pack(anchor='w', pady=(30, 15))
        
        # Status filter
        filter_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Status:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Segoe UI', 10))
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.pack(fill=tk.X, pady=(5, 0))
        
        # Priority filter
        priority_frame = tk.Frame(sidebar_frame, bg=self.colors['sidebar'])
        priority_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(priority_frame, text="Priority:", font=('Segoe UI', 10, 'bold'), 
                fg=self.colors['white'], bg=self.colors['sidebar']).pack(anchor='w')
        
        self.priority_filter = ttk.Combobox(priority_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Segoe UI', 10))
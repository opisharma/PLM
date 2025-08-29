import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json
from pathlib import Path

# Simulated database connection for demo purposes
class DatabaseManager:
    def __init__(self):
        self.data_file = Path("goals_data.json")
        self.data = self.load_data()
    
    def load_data(self):
        """Load data from JSON file"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"goals": [], "progress": [], "next_id": 1}
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
            return True
        except:
            return False
    
    def get_next_id(self):
        """Get next available ID"""
        current_id = self.data["next_id"]
        self.data["next_id"] += 1
        return current_id


class GoalsManager:
    def __init__(self):
        self.db = DatabaseManager()
        
    def create_goal(self, user_id: int, title: str, description: str = None, 
                   goal_type: str = "general", target_value: float = None, 
                   deadline: str = None, priority: str = "Medium") -> int:
        """Create a new goal"""
        try:
            goal_id = self.db.get_next_id()
            goal = {
                "id": goal_id,
                "user_id": user_id,
                "title": title,
                "description": description,
                "goal_type": goal_type,
                "target_value": target_value,
                "current_value": 0,
                "progress_percentage": 0,
                "deadline": deadline,
                "status": "Active",
                "priority": priority,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.db.data["goals"].append(goal)
            self.db.save_data()
            return goal_id
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to create goal: {err}")
            return None
    
    def get_goals(self, user_id: int, status: str = None) -> List[Dict]:
        """Get user goals"""
        try:
            goals = [g for g in self.db.data["goals"] if g["user_id"] == user_id]
            if status:
                goals = [g for g in goals if g["status"] == status]
            return sorted(goals, key=lambda x: x["created_at"], reverse=True)
        except Exception as err:
            messagebox.showerror("Error", f"Failed to get goals: {err}")
            return []
    
    def get_goal_by_id(self, goal_id: int, user_id: int) -> Dict:
        """Get specific goal"""
        try:
            for goal in self.db.data["goals"]:
                if goal["id"] == goal_id and goal["user_id"] == user_id:
                    return goal
            return None
        except Exception as err:
            messagebox.showerror("Error", f"Failed to get goal: {err}")
            return None
    
    def update_goal_progress(self, goal_id: int, user_id: int, current_value: float, 
                           notes: str = None) -> bool:
        """Update goal progress"""
        try:
            goal = self.get_goal_by_id(goal_id, user_id)
            if not goal:
                return False
            
            target_value = goal['target_value']
            if target_value and target_value > 0:
                progress_percentage = min(100, int((current_value / target_value) * 100))
            else:
                progress_percentage = 0
            
            # Update goal
            for i, g in enumerate(self.db.data["goals"]):
                if g["id"] == goal_id and g["user_id"] == user_id:
                    self.db.data["goals"][i]["current_value"] = current_value
                    self.db.data["goals"][i]["progress_percentage"] = progress_percentage
                    self.db.data["goals"][i]["updated_at"] = datetime.now().isoformat()
                    break
            
            # Add progress record
            progress_record = {
                "goal_id": goal_id,
                "user_id": user_id,
                "progress_percentage": progress_percentage,
                "notes": notes,
                "created_at": datetime.now().isoformat()
            }
            self.db.data["progress"].append(progress_record)
            
            self.db.save_data()
            
            if progress_percentage >= 100:
                self.complete_goal(goal_id, user_id)
            
            return True
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to update progress: {err}")
            return False
    
    def complete_goal(self, goal_id: int, user_id: int) -> bool:
        """Complete a goal"""
        try:
            for i, goal in enumerate(self.db.data["goals"]):
                if goal["id"] == goal_id and goal["user_id"] == user_id:
                    self.db.data["goals"][i]["status"] = "Completed"
                    self.db.data["goals"][i]["updated_at"] = datetime.now().isoformat()
                    break
            
            self.db.save_data()
            return True
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to complete goal: {err}")
            return False
    
    def delete_goal(self, goal_id: int, user_id: int) -> bool:
        """Delete a goal"""
        try:
            # Remove goal
            self.db.data["goals"] = [g for g in self.db.data["goals"] 
                                   if not (g["id"] == goal_id and g["user_id"] == user_id)]
            
            # Remove related progress records
            self.db.data["progress"] = [p for p in self.db.data["progress"] 
                                      if p["goal_id"] != goal_id]
            
            self.db.save_data()
            return True
                
        except Exception as err:
            messagebox.showerror("Error", f"Failed to delete goal: {err}")
            return False
    
    def get_user_goal_stats(self, user_id: int) -> Dict:
        """Get user goal statistics"""
        try:
            goals = [g for g in self.db.data["goals"] if g["user_id"] == user_id]
            total_goals = len(goals)
            completed_goals = len([g for g in goals if g["status"] == "Completed"])
            active_goals = len([g for g in goals if g["status"] == "Active"])
            
            active_goals_list = [g for g in goals if g["status"] == "Active"]
            avg_progress = sum(g["progress_percentage"] for g in active_goals_list) / len(active_goals_list) if active_goals_list else 0
            
            return {
                'total_goals': total_goals,
                'completed_goals': completed_goals,
                'active_goals': active_goals,
                'completion_rate': (completed_goals / total_goals * 100) if total_goals > 0 else 0,
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
        
        # Current user (in real app, this would come from login)
        self.current_user_id = 1
        
        # Configure styles
        self.setup_modern_styles()
        
        # Create modern GUI
        self.create_modern_layout()
        
        # Load initial data
        self.refresh_goals_list()
        
        # Set window icon and properties
        self.root.iconname("Goals Manager")
        self.root.minsize(1200, 700)
    
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
        subtitle_label = ttk.Label(header_frame, text="Professional  Edition", 
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
        """Create main content area with goals table"""
        # Main content container
        content_container = tk.Frame(self.content_frame, bg=self.colors['background'])
        content_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Content header
        header_frame = tk.Frame(content_container, bg=self.colors['background'], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Page title
        ttk.Label(header_frame, text="📋 Goals Overview", 
                 font=('Segoe UI', 18, 'bold'), foreground=self.colors['primary']).place(y=15)
        
        # Search and actions bar
        actions_frame = tk.Frame(header_frame, bg=self.colors['background'])
        actions_frame.place(rely=1.0, relx=1.0, anchor='se', y=-10)
        
        # Search box
        search_label = tk.Label(actions_frame, text="🔍", font=('Segoe UI', 12), 
                              bg=self.colors['background'], fg=self.colors['dark'])
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(actions_frame, textvariable=self.search_var, 
                              font=('Segoe UI', 10), width=25)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind('<KeyRelease>', self.on_search)
        
        # Goals table container with modern styling
        table_container = ttk.Frame(content_container, style='Modern.TFrame')
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Table header
        table_header = tk.Frame(table_container, bg=self.colors['card'], height=40)
        table_header.pack(fill=tk.X, padx=20, pady=20)
        table_header.pack_propagate(False)
        
        tk.Label(table_header, text="Goals List", font=('Segoe UI', 14, 'bold'), 
                bg=self.colors['card'], fg=self.colors['primary']).place(y=10)
        
        # Modern treeview
        self.create_modern_table(table_container)
    
    def create_modern_table(self, parent):
        """Create modern styled table"""
        # Table frame with scrollbars
        table_frame = tk.Frame(parent, bg=self.colors['card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview with modern styling
        columns = ('ID', 'Title', 'Type', 'Priority', 'Progress', 'Status', 'Deadline', 'Created')
        self.goals_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Configure modern column styles
        column_configs = {
            'ID': {'width': 60, 'anchor': 'center'},
            'Title': {'width': 250, 'anchor': 'w'},
            'Type': {'width': 100, 'anchor': 'center'},
            'Priority': {'width': 80, 'anchor': 'center'},
            'Progress': {'width': 100, 'anchor': 'center'},
            'Status': {'width': 100, 'anchor': 'center'},
            'Deadline': {'width': 120, 'anchor': 'center'},
            'Created': {'width': 120, 'anchor': 'center'}
        }
        
        for col in columns:
            self.goals_tree.heading(col, text=col, anchor='w')
            config = column_configs.get(col, {'width': 100, 'anchor': 'w'})
            self.goals_tree.column(col, width=config['width'], anchor=config['anchor'])
        
        # Modern scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.goals_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.goals_tree.xview)
        self.goals_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.goals_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Context menu and double-click
        self.goals_tree.bind('<Double-1>', self.show_goal_details)
        self.goals_tree.bind('<Button-3>', self.show_context_menu)
    
    def create_status_bar(self):
        """Create modern status bar"""
        status_frame = tk.Frame(self.main_container, bg=self.colors['light'], height=30)
        status_frame.pack(fill=tk.X, pady=(20, 0))
        status_frame.pack_propagate(False)
        
        # Status text
        self.status_text = tk.StringVar()
        self.status_text.set("Ready")
        
        status_label = tk.Label(status_frame, textvariable=self.status_text, 
                              font=('Segoe UI', 9), bg=self.colors['light'], fg=self.colors['dark'])
        status_label.place(x=10, rely=0.5, anchor='w')
        
        # Last updated
        self.last_updated = tk.StringVar()
        self.last_updated.set(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        updated_label = tk.Label(status_frame, textvariable=self.last_updated, 
                               font=('Segoe UI', 9), bg=self.colors['light'], fg=self.colors['dark'])
        updated_label.place(relx=1.0, rely=0.5, anchor='e', x=-10)
    
    def on_search(self, event=None):
        """Handle search functionality"""
        search_term = self.search_var.get().lower()
        self.refresh_goals_list(search_term)
    
    def show_context_menu(self, event):
        """Show context menu for table items"""
        try:
            item = self.goals_tree.selection()[0]
            
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="📋 View Details", command=self.show_goal_details)
            context_menu.add_command(label="📈 Update Progress", command=self.update_progress_dialog)
            context_menu.add_command(label="✅ Mark Complete", command=self.complete_goal_dialog)
            context_menu.add_separator()
            context_menu.add_command(label="🗑️ Delete Goal", command=self.delete_goal_dialog)
            
            context_menu.post(event.x_root, event.y_root)
        except IndexError:
            pass
    
    def refresh_goals_list(self, search_term=""):
        """Refresh goals list with modern styling"""
        # Clear existing items
        for item in self.goals_tree.get_children():
            self.goals_tree.delete(item)
        
        # Get filter values
        status_filter = self.status_filter.get()
        priority_filter = self.priority_filter.get()
        status = None if status_filter == "All" else status_filter
        
        # Get goals from database
        goals = self.gm.get_goals(self.current_user_id, status)
        
        # Apply filters
        if priority_filter != "All":
            goals = [g for g in goals if g['priority'] == priority_filter]
        
        if search_term:
            goals = [g for g in goals if search_term in g['title'].lower() or 
                    search_term in (g['description'] or '').lower()]
        
        # Populate treeview with modern styling
        for goal in goals:
            # Format dates
            created_date = datetime.fromisoformat(goal['created_at']).strftime('%Y-%m-%d')
            deadline_str = goal['deadline'] if goal['deadline'] else "No deadline"
            
            values = (
                goal['id'],
                goal['title'][:35] + "..." if len(goal['title']) > 35 else goal['title'],
                goal['goal_type'].title(),
                goal['priority'],
                f"{goal['progress_percentage']}%",
                goal['status'],
                deadline_str,
                created_date
            )
            
            # Modern color coding
            tags = []
            if goal['status'] == 'Completed':
                tags.append('completed')
            elif goal['priority'] == 'High':
                tags.append('high_priority')
            elif goal['progress_percentage'] >= 75:
                tags.append('high_progress')
            elif goal['progress_percentage'] >= 25:
                tags.append('medium_progress')
            else:
                tags.append('low_progress')
            
            self.goals_tree.insert('', tk.END, values=values, tags=tags)
        
        # Configure modern tags
        self.goals_tree.tag_configure('completed', background='#d4edda', foreground='#155724')
        self.goals_tree.tag_configure('high_priority', background='#f8d7da', foreground='#721c24')
        self.goals_tree.tag_configure('high_progress', background='#d1ecf1', foreground='#0c5460')
        self.goals_tree.tag_configure('medium_progress', background='#fff3cd', foreground='#856404')
        self.goals_tree.tag_configure('low_progress', background='#f2f2f2', foreground='#6c757d')
        
        # Update status
        self.status_text.set(f"Showing {len(goals)} goals")
        self.last_updated.set(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        # Refresh sidebar stats
        self.refresh_sidebar_stats()
    
    def refresh_sidebar_stats(self):
        """Refresh sidebar statistics"""
        # Find and update sidebar stats
        for widget in self.root.winfo_children():
            if hasattr(widget, 'winfo_children'):
                self.update_sidebar_stats_recursive(widget)
    
    def update_sidebar_stats_recursive(self, widget):
        """Recursively update sidebar stats"""
        try:
            # This is a simplified approach - in a real app you'd have better widget management
            pass
        except:
            pass
    
    def create_goal_dialog(self):
        """Modern goal creation dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Goal")
        dialog.geometry("600x500")
        dialog.configure(bg=self.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 200, self.root.winfo_rooty() + 100))
        
        # Main container
        main_frame = tk.Frame(dialog, bg=self.colors['background'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        tk.Label(header_frame, text="➕ Create New Goal", 
                font=('Segoe UI', 18, 'bold'), bg=self.colors['background'], 
                fg=self.colors['primary']).pack(anchor='w')
        
        tk.Label(header_frame, text="Define your new goal with clear objectives and timeline", 
                font=('Segoe UI', 10), bg=self.colors['background'], 
                fg=self.colors['dark']).pack(anchor='w', pady=(5, 0))
        
        # Form container
        form_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='solid', borderwidth=1)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        form_inner = tk.Frame(form_frame, bg=self.colors['card'])
        form_inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        fields = {}
        row = 0
        
        # Title field
        tk.Label(form_inner, text="Goal Title *", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).grid(row=row, column=0, sticky='w', pady=(0, 5))
        fields['title'] = tk.Entry(form_inner, font=('Segoe UI', 11), width=50, relief='solid', borderwidth=1)
        fields['title'].grid(row=row+1, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        
        # Description field
        row += 2
        tk.Label(form_inner, text="Description", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).grid(row=row, column=0, sticky='w', pady=(0, 5))
        
        desc_frame = tk.Frame(form_inner, bg=self.colors['card'])
        desc_frame.grid(row=row+1, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        
        fields['description'] = tk.Text(desc_frame, height=4, font=('Segoe UI', 10), 
                                       relief='solid', borderwidth=1, wrap=tk.WORD)
        desc_scroll = tk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=fields['description'].yview)
        fields['description'].configure(yscrollcommand=desc_scroll.set)
        
        fields['description'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Two-column layout for remaining fields
        row += 2
        left_col = tk.Frame(form_inner, bg=self.colors['card'])
        left_col.grid(row=row, column=0, sticky='ew', padx=(0, 10))
        
        right_col = tk.Frame(form_inner, bg=self.colors['card'])
        right_col.grid(row=row, column=1, sticky='ew', padx=(10, 0))
        
        form_inner.columnconfigure(0, weight=1)
        form_inner.columnconfigure(1, weight=1)
        
        # Goal Type
        tk.Label(left_col, text="Goal Type", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 5))
        fields['goal_type'] = ttk.Combobox(left_col, values=["General", "Fitness", "Career", "Personal", "Financial"], 
                                          state="readonly", font=('Segoe UI', 10))
        fields['goal_type'].set("General")
        fields['goal_type'].pack(fill=tk.X, pady=(0, 15))
        
        # Priority
        tk.Label(left_col, text="Priority Level", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 5))
        fields['priority'] = ttk.Combobox(left_col, values=["Low", "Medium", "High"], 
                                         state="readonly", font=('Segoe UI', 10))
        fields['priority'].set("Medium")
        fields['priority'].pack(fill=tk.X, pady=(0, 15))
        
        # Target Value
        tk.Label(right_col, text="Target Value", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 5))
        fields['target_value'] = tk.Entry(right_col, font=('Segoe UI', 10), relief='solid', borderwidth=1)
        fields['target_value'].pack(fill=tk.X, pady=(0, 15))
        
        # Deadline
        tk.Label(right_col, text="Deadline (YYYY-MM-DD)", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 5))
        fields['deadline'] = tk.Entry(right_col, font=('Segoe UI', 10), relief='solid', borderwidth=1)
        fields['deadline'].pack(fill=tk.X, pady=(0, 15))
        
        def create_goal():
            title = fields['title'].get().strip()
            if not title:
                messagebox.showerror("Validation Error", "Goal title is required!")
                fields['title'].focus()
                return
            
            description = fields['description'].get(1.0, tk.END).strip() or None
            goal_type = fields['goal_type'].get().lower()
            priority = fields['priority'].get()
            
            try:
                target_value = float(fields['target_value'].get()) if fields['target_value'].get().strip() else None
            except ValueError:
                messagebox.showerror("Validation Error", "Target value must be a number!")
                fields['target_value'].focus()
                return
            
            deadline = fields['deadline'].get().strip() or None
            
            # Validate deadline format
            if deadline:
                try:
                    datetime.strptime(deadline, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Validation Error", "Deadline must be in YYYY-MM-DD format!")
                    fields['deadline'].focus()
                    return
            
            goal_id = self.gm.create_goal(self.current_user_id, title, description, 
                                        goal_type, target_value, deadline, priority)
            
            if goal_id:
                messagebox.showinfo("Success", f"✅ Goal created successfully!\n\nGoal ID: {goal_id}")
                dialog.destroy()
                self.refresh_goals_list()
                self.status_text.set("New goal created successfully")
            else:
                messagebox.showerror("Error", "❌ Failed to create goal. Please try again.")
        
        def cancel():
            dialog.destroy()
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['background'])
        button_frame.pack(fill=tk.X)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=cancel,
                              font=('Segoe UI', 11), bg=self.colors['light'], 
                              fg=self.colors['dark'], relief='solid', borderwidth=1,
                              padx=20, pady=8)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        create_btn = tk.Button(button_frame, text="Create Goal", command=create_goal,
                              font=('Segoe UI', 11, 'bold'), bg=self.colors['secondary'], 
                              fg=self.colors['white'], relief='solid', borderwidth=1,
                              padx=20, pady=8)
        create_btn.pack(side=tk.RIGHT)
        
        # Focus on title field
        fields['title'].focus()
        
        # Enter key binding
        dialog.bind('<Return>', lambda e: create_goal())
        dialog.bind('<Escape>', lambda e: cancel())
    
    def update_progress_dialog(self):
        """Modern progress update dialog"""
        selected = self.goals_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a goal to update progress!")
            return
        
        goal_id = self.goals_tree.item(selected[0])['values'][0]
        goal = self.gm.get_goal_by_id(goal_id, self.current_user_id)
        
        if not goal:
            messagebox.showerror("Error", "Goal not found!")
            return
        
        if goal['status'] == 'Completed':
            messagebox.showinfo("Information", "This goal is already completed!")
            return
        
        # Modern dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Goal Progress")
        dialog.geometry("550x400")
        dialog.configure(bg=self.colors['background'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 250, self.root.winfo_rooty() + 150))
        
        main_frame = tk.Frame(dialog, bg=self.colors['background'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(header_frame, text="📈 Update Progress", 
                font=('Segoe UI', 18, 'bold'), bg=self.colors['background'], 
                fg=self.colors['primary']).pack(anchor='w')
        
        tk.Label(header_frame, text=f"Goal: {goal['title']}", 
                font=('Segoe UI', 12), bg=self.colors['background'], 
                fg=self.colors['dark']).pack(anchor='w', pady=(5, 0))
        
        # Goal info card
        info_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='solid', borderwidth=1)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_inner = tk.Frame(info_frame, bg=self.colors['card'])
        info_inner.pack(fill=tk.X, padx=20, pady=15)
        
        # Current progress info
        tk.Label(info_inner, text="Current Status", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w')
        
        current_info = f"Target: {goal['target_value'] or 'No target set'}\n"
        current_info += f"Current: {goal['current_value']}\n"
        current_info += f"Progress: {goal['progress_percentage']}%"
        
        tk.Label(info_inner, text=current_info, font=('Segoe UI', 10), 
                bg=self.colors['card'], fg=self.colors['dark'], justify='left').pack(anchor='w', pady=(5, 10))
        
        # Progress bar
        progress_frame = tk.Frame(info_inner, bg=self.colors['card'])
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        progress_bar['value'] = goal['progress_percentage']
        progress_bar.pack()
        
        tk.Label(progress_frame, text=f"{goal['progress_percentage']}% Complete", 
                font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], 
                fg=self.colors['secondary']).pack(pady=(5, 0))
        
        # Update form
        form_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='solid', borderwidth=1)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        form_inner = tk.Frame(form_frame, bg=self.colors['card'])
        form_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # New value
        tk.Label(form_inner, text="New Current Value *", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 5))
        
        value_entry = tk.Entry(form_inner, font=('Segoe UI', 12), relief='solid', 
                              borderwidth=1, width=20)
        value_entry.pack(anchor='w', pady=(0, 15))
        value_entry.insert(0, str(goal['current_value']))
        
        # Notes
        tk.Label(form_inner, text="Progress Notes (Optional)", font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 5))
        
        notes_frame = tk.Frame(form_inner, bg=self.colors['card'])
        notes_frame.pack(fill=tk.BOTH, expand=True)
        
        notes_text = tk.Text(notes_frame, height=4, font=('Segoe UI', 10), 
                            relief='solid', borderwidth=1, wrap=tk.WORD)
        notes_scroll = tk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=notes_text.yview)
        notes_text.configure(yscrollcommand=notes_scroll.set)
        
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notes_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        def update_progress():
            try:
                current_value = float(value_entry.get())
            except ValueError:
                messagebox.showerror("Validation Error", "Please enter a valid number!")
                value_entry.focus()
                return
            
            notes = notes_text.get(1.0, tk.END).strip() or None
            
            if self.gm.update_goal_progress(goal_id, self.current_user_id, current_value, notes):
                messagebox.showinfo("Success", "✅ Progress updated successfully!")
                dialog.destroy()
                self.refresh_goals_list()
                self.status_text.set("Goal progress updated")
            else:
                messagebox.showerror("Error", "❌ Failed to update progress!")
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['background'])
        button_frame.pack(fill=tk.X)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                              font=('Segoe UI', 11), bg=self.colors['light'], 
                              fg=self.colors['dark'], relief='solid', borderwidth=1,
                              padx=20, pady=8)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        update_btn = tk.Button(button_frame, text="Update Progress", command=update_progress,
                              font=('Segoe UI', 11, 'bold'), bg=self.colors['success'], 
                              fg=self.colors['white'], relief='solid', borderwidth=1,
                              padx=20, pady=8)
        update_btn.pack(side=tk.RIGHT)
        
        # Focus and bindings
        value_entry.focus()
        value_entry.select_range(0, tk.END)
        dialog.bind('<Return>', lambda e: update_progress())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def complete_goal_dialog(self):
        """Modern goal completion dialog"""
        selected = self.goals_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a goal to mark as complete!")
            return
        
        goal_id = self.goals_tree.item(selected[0])['values'][0]
        goal_title = self.goals_tree.item(selected[0])['values'][1]
        
        # Custom confirmation dialog
        result = messagebox.askyesno("Confirm Completion", 
                                   f"✅ Mark '{goal_title}' as completed?\n\nThis action will mark the goal as 100% complete.",
                                   icon='question')
        
        if result:
            if self.gm.complete_goal(goal_id, self.current_user_id):
                messagebox.showinfo("Congratulations! 🎉", 
                                  f"Goal '{goal_title}' has been marked as completed!\n\nGreat job on achieving your goal!")
                self.refresh_goals_list()
                self.status_text.set("Goal marked as completed")
    
    def delete_goal_dialog(self):
        """Modern goal deletion dialog"""
        selected = self.goals_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a goal to delete!")
            return
        
        goal_id = self.goals_tree.item(selected[0])['values'][0]
        goal_title = self.goals_tree.item(selected[0])['values'][1]
        
        # Custom warning dialog
        result = messagebox.askyesno("Confirm Deletion", 
                                   f"⚠️ Delete '{goal_title}'?\n\nThis action cannot be undone and will permanently remove the goal and all its progress data.",
                                   icon='warning')
        
        if result:
            if self.gm.delete_goal(goal_id, self.current_user_id):
                messagebox.showinfo("Deleted", f"Goal '{goal_title}' has been deleted successfully.")
                self.refresh_goals_list()
                self.status_text.set("Goal deleted successfully")
    
    def show_goal_details(self, event=None):
        """Modern goal details window"""
        selected = self.goals_tree.selection()
        if not selected:
            return
        
        goal_id = self.goals_tree.item(selected[0])['values'][0]
        goal = self.gm.get_goal_by_id(goal_id, self.current_user_id)
        
        if not goal:
            return
        
        # Details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Goal Details - {goal['title']}")
        details_window.geometry("700x600")
        details_window.configure(bg=self.colors['background'])
        
        main_frame = tk.Frame(details_window, bg=self.colors['background'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(header_frame, text="📋 Goal Details", 
                font=('Segoe UI', 18, 'bold'), bg=self.colors['background'], 
                fg=self.colors['primary']).pack(anchor='w')
        
        # Goal card
        card_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='solid', borderwidth=1)
        card_frame.pack(fill=tk.BOTH, expand=True)
        
        card_inner = tk.Frame(card_frame, bg=self.colors['card'])
        card_inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Title section
        title_frame = tk.Frame(card_inner, bg=self.colors['card'])
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(title_frame, text=goal['title'], font=('Segoe UI', 16, 'bold'), 
                bg=self.colors['card'], fg=self.colors['primary'], wraplength=600).pack(anchor='w')
        
        # Status badge
        status_color = self.colors['success'] if goal['status'] == 'Completed' else self.colors['warning']
        status_frame = tk.Frame(title_frame, bg=status_color, height=25)
        status_frame.pack(anchor='w', pady=(10, 0))
        status_frame.pack_propagate(False)
        
        tk.Label(status_frame, text=f"  {goal['status']}  ", 
                font=('Segoe UI', 9, 'bold'), bg=status_color, fg=self.colors['white']).pack(pady=3)
        
        # Description
        if goal['description']:
            tk.Label(card_inner, text="Description", font=('Segoe UI', 12, 'bold'), 
                    bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 5))
            
            desc_text = tk.Text(card_inner, height=4, font=('Segoe UI', 10), 
                               bg=self.colors['light'], relief='flat', wrap=tk.WORD, state='disabled')
            desc_text.pack(fill=tk.X, pady=(0, 20))
            desc_text.configure(state='normal')
            desc_text.insert(1.0, goal['description'])
            desc_text.configure(state='disabled')
        
        # Progress section
        progress_frame = tk.Frame(card_inner, bg=self.colors['card'])
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(progress_frame, text="Progress Overview", font=('Segoe UI', 12, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 10))
        
        # Progress bar
        progress_bar = ttk.Progressbar(progress_frame, length=500, mode='determinate')
        progress_bar['value'] = goal['progress_percentage']
        progress_bar.pack(anchor='w', pady=(0, 5))
        
        tk.Label(progress_frame, text=f"{goal['progress_percentage']}% Complete", 
                font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], 
                fg=self.colors['secondary']).pack(anchor='w')
        
        # Details grid
        details_frame = tk.Frame(card_inner, bg=self.colors['card'])
        details_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Configure grid
        for i in range(4):
            details_frame.columnconfigure(i, weight=1)
        
        details_info = [
            ("Type:", goal['goal_type'].title()),
            ("Priority:", goal['priority']),
            ("Target:", str(goal['target_value']) if goal['target_value'] else "No target"),
            ("Current:", str(goal['current_value'])),
            ("Created:", datetime.fromisoformat(goal['created_at']).strftime('%Y-%m-%d %H:%M')),
            ("Updated:", datetime.fromisoformat(goal['updated_at']).strftime('%Y-%m-%d %H:%M')),
            ("Deadline:", goal['deadline'] if goal['deadline'] else "No deadline"),
            ("Status:", goal['status'])
        ]
        
        for i, (label, value) in enumerate(details_info):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(details_frame, text=label, font=('Segoe UI', 10, 'bold'), 
                    bg=self.colors['card'], fg=self.colors['dark']).grid(row=row, column=col, sticky='w', padx=(0, 10), pady=5)
            
            tk.Label(details_frame, text=value, font=('Segoe UI', 10), 
                    bg=self.colors['card'], fg=self.colors['dark']).grid(row=row, column=col+1, sticky='w', padx=(0, 20), pady=5)
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['background'])
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        if goal['status'] != 'Completed':
            update_btn = tk.Button(button_frame, text="📈 Update Progress", 
                                 command=lambda: [details_window.destroy(), self.update_progress_dialog()],
                                 font=('Segoe UI', 10, 'bold'), bg=self.colors['secondary'], 
                                 fg=self.colors['white'], relief='solid', borderwidth=1, padx=15, pady=8)
            update_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            complete_btn = tk.Button(button_frame, text="✅ Mark Complete", 
                                   command=lambda: [details_window.destroy(), self.complete_goal_dialog()],
                                   font=('Segoe UI', 10, 'bold'), bg=self.colors['success'], 
                                   fg=self.colors['white'], relief='solid', borderwidth=1, padx=15, pady=8)
            complete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = tk.Button(button_frame, text="Close", command=details_window.destroy,
                             font=('Segoe UI', 10), bg=self.colors['light'], 
                             fg=self.colors['dark'], relief='solid', borderwidth=1, padx=15, pady=8)
        close_btn.pack(side=tk.RIGHT)
    
    def show_detailed_statistics(self):
        """Modern detailed statistics window"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            messagebox.showinfo("Statistics", "No statistics available!")
            return
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Goal Analytics Dashboard")
        stats_window.geometry("800x600")
        stats_window.configure(bg=self.colors['background'])
        
        main_frame = tk.Frame(stats_window, bg=self.colors['background'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        tk.Label(header_frame, text="📊 Analytics Dashboard", 
                font=('Segoe UI', 20, 'bold'), bg=self.colors['background'], 
                fg=self.colors['primary']).pack(anchor='w')
        
        tk.Label(header_frame, text="Comprehensive overview of your goal management performance", 
                font=('Segoe UI', 11), bg=self.colors['background'], 
                fg=self.colors['dark']).pack(anchor='w', pady=(5, 0))
        
        # Stats cards container
        cards_container = tk.Frame(main_frame, bg=self.colors['background'])
        cards_container.pack(fill=tk.X, pady=(0, 30))
        
        # Configure grid for cards
        for i in range(4):
            cards_container.columnconfigure(i, weight=1)
        
        # Create stat cards
        stat_cards = [
            ("Total Goals", stats['total_goals'], self.colors['secondary'], "📋"),
            ("Completed", stats['completed_goals'], self.colors['success'], "✅"),
            ("Active Goals", stats['active_goals'], self.colors['warning'], "🔄"),
            ("Success Rate", f"{stats['completion_rate']:.1f}%", self.colors['success'], "📈")
        ]
        
        for i, (title, value, color, icon) in enumerate(stat_cards):
            card = tk.Frame(cards_container, bg=color, relief='solid', borderwidth=1, height=120, width=150)
            card.grid(row=0, column=i, padx=10, sticky='ew')
            card.pack_propagate(False)
            
            # Icon
            tk.Label(card, text=icon, font=('Segoe UI', 20), 
                    bg=color, fg=self.colors['white']).place(relx=0.5, rely=0.25, anchor='center')
            
            # Value
            tk.Label(card, text=str(value), font=('Segoe UI', 18, 'bold'), 
                    bg=color, fg=self.colors['white']).place(relx=0.5, rely=0.55, anchor='center')
            
            # Title
            tk.Label(card, text=title, font=('Segoe UI', 10), 
                    bg=color, fg=self.colors['white']).place(relx=0.5, rely=0.8, anchor='center')
        
        # Detailed stats
        details_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='solid', borderwidth=1)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        details_inner = tk.Frame(details_frame, bg=self.colors['card'])
        details_inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        tk.Label(details_inner, text="📈 Performance Metrics", 
                font=('Segoe UI', 14, 'bold'), bg=self.colors['card'], 
                fg=self.colors['primary']).pack(anchor='w', pady=(0, 20))
        
        # Get additional statistics
        goals = self.gm.get_goals(self.current_user_id)
        
        # Goals by type
        type_stats = {}
        priority_stats = {}
        
        for goal in goals:
            goal_type = goal['goal_type']
            priority = goal['priority']
            
            type_stats[goal_type] = type_stats.get(goal_type, 0) + 1
            priority_stats[priority] = priority_stats.get(priority, 0) + 1
        
        # Create two-column layout for detailed stats
        left_details = tk.Frame(details_inner, bg=self.colors['card'])
        left_details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        right_details = tk.Frame(details_inner, bg=self.colors['card'])
        right_details.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Goals by type
        tk.Label(left_details, text="Goals by Type", font=('Segoe UI', 12, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 10))
        
        for goal_type, count in type_stats.items():
            type_frame = tk.Frame(left_details, bg=self.colors['card'])
            type_frame.pack(fill=tk.X, pady=2)
            
            tk.Label(type_frame, text=f"{goal_type.title()}:", 
                    font=('Segoe UI', 10), bg=self.colors['card'], 
                    fg=self.colors['dark']).pack(side=tk.LEFT)
            
            tk.Label(type_frame, text=str(count), 
                    font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], 
                    fg=self.colors['secondary']).pack(side=tk.RIGHT)
        
        # Goals by priority
        tk.Label(right_details, text="Goals by Priority", font=('Segoe UI', 12, 'bold'), 
                bg=self.colors['card'], fg=self.colors['dark']).pack(anchor='w', pady=(0, 10))
        
        priority_colors = {'High': self.colors['danger'], 'Medium': self.colors['warning'], 'Low': self.colors['success']}
        
        for priority, count in priority_stats.items():
            priority_frame = tk.Frame(right_details, bg=self.colors['card'])
            priority_frame.pack(fill=tk.X, pady=2)
            
            # Priority indicator
            indicator = tk.Frame(priority_frame, bg=priority_colors.get(priority, self.colors['secondary']), 
                               width=10, height=15)
            indicator.pack(side=tk.LEFT, padx=(0, 10))
            
            tk.Label(priority_frame, text=f"{priority}:", 
                    font=('Segoe UI', 10), bg=self.colors['card'], 
                    fg=self.colors['dark']).pack(side=tk.LEFT)
            
            tk.Label(priority_frame, text=str(count), 
                    font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], 
                    fg=self.colors['secondary']).pack(side=tk.RIGHT)
        
        # Additional metrics
        if stats['active_goals'] > 0:
            metrics_frame = tk.Frame(details_inner, bg=self.colors['card'])
            metrics_frame.pack(fill=tk.X, pady=(30, 0))
            
            tk.Label(metrics_frame, text="Additional Insights", 
                    font=('Segoe UI', 12, 'bold'), bg=self.colors['card'], 
                    fg=self.colors['dark']).pack(anchor='w', pady=(0, 10))
            
            # Average progress
            avg_frame = tk.Frame(metrics_frame, bg=self.colors['card'])
            avg_frame.pack(fill=tk.X, pady=2)
            
            tk.Label(avg_frame, text="Average Progress:", 
                    font=('Segoe UI', 10), bg=self.colors['card'], 
                    fg=self.colors['dark']).pack(side=tk.LEFT)
            
            tk.Label(avg_frame, text=f"{stats['average_progress']}%", 
                    font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], 
                    fg=self.colors['secondary']).pack(side=tk.RIGHT)
            
            # Progress bar for average
            avg_progress_bar = ttk.Progressbar(metrics_frame, length=400, mode='determinate')
            avg_progress_bar['value'] = stats['average_progress']
            avg_progress_bar.pack(pady=(10, 0))
        
        # Close button
        close_frame = tk.Frame(main_frame, bg=self.colors['background'])
        close_frame.pack(fill=tk.X, pady=(20, 0))
        
        close_btn = tk.Button(close_frame, text="Close", command=stats_window.destroy,
                             font=('Segoe UI', 11), bg=self.colors['secondary'], 
                             fg=self.colors['white'], relief='solid', borderwidth=1,
                             padx=30, pady=10)
        close_btn.pack(side=tk.RIGHT)
    
    def run(self):
        """Run the modern GUI application"""
        try:
            # Set initial status
            self.status_text.set("Application ready")
            
            # Start the GUI
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Application Error", f"An error occurred: {e}")
        finally:
            # Cleanup if needed
            try:
                self.gm.db.save_data()
            except:
                pass


def main():
    """Main application entry point"""
    try:
        # Create and run the application
        app = ModernGoalsManagerGUI()
        app.run()
    except Exception as e:
        # Handle any startup errors
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        messagebox.showerror("Startup Error", 
                           f"Failed to start the Goals Management System:\n\n{str(e)}\n\nPlease check your system configuration and try again.")
        root.destroy()


if __name__ == "__main__":
    main()
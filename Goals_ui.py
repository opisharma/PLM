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
            print(f"Connect error: {e}")
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
            print(f"Database error: {err}")
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


class UniqueGoalsManagerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ZenGoals - Modern Goal Tracker")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#0a0a0a')
        self.root.state('zoomed')
        
        # Unique dark theme with neon accents
        self.theme = {
            'bg_primary': '#0a0a0a',      # Deep black
            'bg_secondary': '#1a1a1a',    # Dark gray
            'bg_card': '#252525',         # Card background
            'accent_cyan': '#00d4ff',     # Bright cyan
            'accent_purple': '#8b5cf6',   # Purple
            'accent_green': '#10b981',    # Green
            'accent_orange': '#f59e0b',   # Orange
            'accent_red': '#ef4444',      # Red
            'text_primary': '#ffffff',    # White text
            'text_secondary': '#a1a1aa',  # Gray text
            'text_muted': '#71717a',      # Muted text
            'border': '#374151',          # Border color
            'glow': '#00d4ff40'           # Glow effect
        }
        
        self.gm = GoalsManager()
        self.selected_goal_id = None
        
        # Check database connection
        if not self.gm.db.connection:
            messagebox.showerror("Database Error", 
                               "Could not connect to database. Please check your MySQL server.")
            self.root.destroy()
            return
        
        self.current_user_id = 1
        
        # Setup unique styles
        self.setup_unique_styles()
        
        # Create unique layout
        self.create_unique_layout()
        
        # Load data
        self.refresh_dashboard()
        
        # Window properties
        self.root.iconname("ZenGoals")
        self.root.minsize(1400, 800)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Handle application closing"""
        try:
            if self.gm and self.gm.db:
                self.gm.db.close_connection()
        except:
            pass
        finally:
            self.root.destroy()
    
    def setup_unique_styles(self):
        """Setup unique dark theme styles"""
        style = ttk.Style()
        
        # Configure dark theme
        style.theme_use('clam')
        
        # Custom dark styles
        style.configure('Dark.TFrame', background=self.theme['bg_secondary'])
        style.configure('Card.TFrame', background=self.theme['bg_card'], relief='flat')
        
        # Text styles
        style.configure('Title.TLabel', 
                       font=('Roboto', 32, 'bold'), 
                       foreground=self.theme['text_primary'],
                       background=self.theme['bg_primary'])
        
        style.configure('Subtitle.TLabel', 
                       font=('Roboto', 14), 
                       foreground=self.theme['accent_cyan'],
                       background=self.theme['bg_primary'])
        
        style.configure('CardTitle.TLabel', 
                       font=('Roboto', 16, 'bold'), 
                       foreground=self.theme['text_primary'],
                       background=self.theme['bg_card'])
        
        style.configure('StatValue.TLabel', 
                       font=('Roboto', 28, 'bold'), 
                       foreground=self.theme['accent_cyan'],
                       background=self.theme['bg_card'])
        
        style.configure('StatLabel.TLabel', 
                       font=('Roboto', 12), 
                       foreground=self.theme['text_secondary'],
                       background=self.theme['bg_card'])
        
        # Button styles
        style.configure('Neon.TButton',
                       font=('Roboto', 11, 'bold'),
                       padding=(25, 12),
                       borderwidth=0)
        
        style.map('Neon.TButton',
                 background=[('active', self.theme['accent_cyan']),
                            ('!active', self.theme['bg_card'])],
                 foreground=[('active', self.theme['bg_primary']),
                            ('!active', self.theme['accent_cyan'])])
        
        # Treeview dark theme
        style.configure('Dark.Treeview',
                       background=self.theme['bg_card'],
                       foreground=self.theme['text_primary'],
                       fieldbackground=self.theme['bg_card'],
                       borderwidth=0,
                       font=('Roboto', 10))
        
        style.configure('Dark.Treeview.Heading',
                       background=self.theme['bg_secondary'],
                       foreground=self.theme['accent_cyan'],
                       font=('Roboto', 11, 'bold'))
        
        style.map('Dark.Treeview',
                 background=[('selected', self.theme['accent_cyan'])],
                 foreground=[('selected', self.theme['bg_primary'])])
    
    def create_unique_layout(self):
        """Create unique modern layout with glassmorphism effects"""
        # Main container
        self.main_container = tk.Frame(self.root, bg=self.theme['bg_primary'])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Animated header
        self.create_animated_header()
        
        # Dashboard grid layout
        self.create_dashboard_grid()
        
        # Floating action panel
        self.create_floating_actions()
        
        # Status indicator
        self.create_status_indicator()
    
    def create_animated_header(self):
        """Create animated header with gradient effect"""
        header_canvas = tk.Canvas(self.main_container, height=120, bg=self.theme['bg_primary'], 
                                highlightthickness=0)
        header_canvas.pack(fill=tk.X, padx=20, pady=(20, 0))
        
        # Gradient background simulation
        for i in range(120):
            alpha = 1 - (i / 120)
            color_intensity = int(alpha * 100)
            if color_intensity > 0:
                color = f"#{color_intensity:02x}{color_intensity:02x}{color_intensity:02x}"
                header_canvas.create_line(0, i, 1600, i, fill=color, width=1)
        
        # Glowing title
        header_canvas.create_text(40, 35, text="ZenGoals", font=('Roboto', 36, 'bold'), 
                                fill=self.theme['accent_cyan'], anchor='w')
        header_canvas.create_text(40, 75, text="Modern Goal Achievement Platform", 
                                font=('Roboto', 14), fill=self.theme['text_secondary'], anchor='w')
        
        # Connection status with pulsing effect
        status_color = self.theme['accent_green'] if self.gm.db.connection else self.theme['accent_red']
        status_text = "CONNECTED" if self.gm.db.connection else "DISCONNECTED"
        header_canvas.create_oval(1450, 45, 1470, 65, fill=status_color, outline=status_color)
        header_canvas.create_text(1480, 55, text=status_text, font=('Roboto', 10, 'bold'), 
                                fill=status_color, anchor='w')
    
    def create_dashboard_grid(self):
        """Create unique dashboard with card-based layout"""
        # Main grid container
        grid_frame = tk.Frame(self.main_container, bg=self.theme['bg_primary'])
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configure grid weights
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=3)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=2)
        
        # Top row: Stats cards
        self.create_stats_dashboard(grid_frame)
        
        # Bottom left: Quick actions
        self.create_action_center(grid_frame)
        
        # Bottom right: Goals visualization
        self.create_goals_visualization(grid_frame)
    
    def create_stats_dashboard(self, parent):
        """Create modern stats dashboard with neon cards"""
        stats_container = tk.Frame(parent, bg=self.theme['bg_primary'])
        stats_container.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        
        # Get stats
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        # Stats cards with neon glow effect
        cards_frame = tk.Frame(stats_container, bg=self.theme['bg_primary'])
        cards_frame.pack(fill=tk.X)
        
        # Configure equal column weights
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)
        
        # Individual stat cards
        stat_configs = [
            ("TOTAL GOALS", stats.get('total_goals', 0), self.theme['accent_cyan'], "Target achievements set"),
            ("COMPLETED", stats.get('completed_goals', 0), self.theme['accent_green'], "Successfully achieved"),
            ("IN PROGRESS", stats.get('active_goals', 0), self.theme['accent_orange'], "Currently working on"),
            ("SUCCESS RATE", f"{stats.get('completion_rate', 0):.0f}%", self.theme['accent_purple'], "Overall performance")
        ]
        
        for i, (title, value, color, subtitle) in enumerate(stat_configs):
            self.create_neon_card(cards_frame, title, value, subtitle, color, i)
    
    def create_neon_card(self, parent, title, value, subtitle, color, column):
        """Create a neon-styled card with glow effect"""
        # Card container with glow simulation
        card_container = tk.Frame(parent, bg=self.theme['bg_primary'])
        card_container.grid(row=0, column=column, padx=15, pady=10, sticky='ew')
        
        # Outer glow frame
        glow_frame = tk.Frame(card_container, bg=color, height=140)
        glow_frame.pack(fill=tk.BOTH, expand=True)
        glow_frame.pack_propagate(False)
        
        # Inner card
        card_frame = tk.Frame(glow_frame, bg=self.theme['bg_card'])
        card_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Card content
        content_frame = tk.Frame(card_frame, bg=self.theme['bg_card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Value (large)
        value_label = tk.Label(content_frame, text=str(value), 
                             font=('Roboto', 28, 'bold'), fg=color, bg=self.theme['bg_card'])
        value_label.pack(anchor='center', pady=(10, 5))
        
        # Title
        title_label = tk.Label(content_frame, text=title, 
                             font=('Roboto', 12, 'bold'), fg=self.theme['text_primary'], 
                             bg=self.theme['bg_card'])
        title_label.pack(anchor='center')
        
        # Subtitle
        subtitle_label = tk.Label(content_frame, text=subtitle, 
                                font=('Roboto', 9), fg=self.theme['text_muted'], 
                                bg=self.theme['bg_card'])
        subtitle_label.pack(anchor='center', pady=(5, 0))
    
    def create_action_center(self, parent):
        """Create action center with modern buttons"""
        action_frame = tk.Frame(parent, bg=self.theme['bg_card'], relief='flat')
        action_frame.grid(row=1, column=0, sticky='nsew', padx=(0, 10))
        
        # Action center header
        header_frame = tk.Frame(action_frame, bg=self.theme['bg_secondary'], height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, text="ACTION CENTER", 
                              font=('Roboto', 16, 'bold'), fg=self.theme['accent_cyan'], 
                              bg=self.theme['bg_secondary'])
        header_label.place(x=20, y=12)
        
        # Action buttons container
        actions_container = tk.Frame(action_frame, bg=self.theme['bg_card'])
        actions_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Modern action buttons
        action_configs = [
            ("NEW GOAL", "Create a new achievement target", self.create_goal_dialog, self.theme['accent_green']),
            ("UPDATE PROGRESS", "Track your advancement", self.update_progress_dialog, self.theme['accent_orange']),
            ("COMPLETE GOAL", "Mark achievement as done", self.complete_goal_dialog, self.theme['accent_purple']),
            ("VIEW ANALYTICS", "Analyze your performance", self.show_analytics, self.theme['accent_cyan']),
            ("DELETE GOAL", "Remove selected goal", self.delete_goal_dialog, self.theme['accent_red'])
        ]
        
        for i, (title, subtitle, command, color) in enumerate(action_configs):
            self.create_action_button(actions_container, title, subtitle, command, color, i)
        
        # Search section
        search_frame = tk.Frame(actions_container, bg=self.theme['bg_card'])
        search_frame.pack(fill=tk.X, pady=(30, 0))
        
        search_label = tk.Label(search_frame, text="SEARCH GOALS", 
                              font=('Roboto', 12, 'bold'), fg=self.theme['text_primary'], 
                              bg=self.theme['bg_card'])
        search_label.pack(anchor='w', pady=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                              font=('Roboto', 12), bg=self.theme['bg_secondary'], 
                              fg=self.theme['text_primary'], insertbackground=self.theme['accent_cyan'],
                              relief='flat', bd=0)
        search_entry.pack(fill=tk.X, ipady=8)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_goals())
        
        # Add border effect to search
        search_border = tk.Frame(search_frame, bg=self.theme['accent_cyan'], height=2)
        search_border.pack(fill=tk.X)
    
    def create_action_button(self, parent, title, subtitle, command, color, index):
        """Create modern action button with hover effects"""
        btn_container = tk.Frame(parent, bg=self.theme['bg_card'])
        btn_container.pack(fill=tk.X, pady=8)
        
        # Button frame with border
        btn_frame = tk.Frame(btn_container, bg=self.theme['bg_secondary'], relief='flat')
        btn_frame.pack(fill=tk.X, ipady=15, ipadx=20)
        
        # Left accent bar
        accent_bar = tk.Frame(btn_frame, bg=color, width=4)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        # Text content
        text_frame = tk.Frame(btn_frame, bg=self.theme['bg_secondary'])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(text_frame, text=title, font=('Roboto', 12, 'bold'), 
                             fg=color, bg=self.theme['bg_secondary'])
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(text_frame, text=subtitle, font=('Roboto', 9), 
                                fg=self.theme['text_muted'], bg=self.theme['bg_secondary'])
        subtitle_label.pack(anchor='w')
        
        # Make entire button clickable
        def on_click(event):
            command()
        
        def on_enter(event):
            btn_frame.config(bg=color)
            title_label.config(bg=color, fg=self.theme['bg_primary'])
            subtitle_label.config(bg=color, fg=self.theme['bg_primary'])
            text_frame.config(bg=color)
        
        def on_leave(event):
            btn_frame.config(bg=self.theme['bg_secondary'])
            title_label.config(bg=self.theme['bg_secondary'], fg=color)
            subtitle_label.config(bg=self.theme['bg_secondary'], fg=self.theme['text_muted'])
            text_frame.config(bg=self.theme['bg_secondary'])
        
        for widget in [btn_frame, text_frame, title_label, subtitle_label]:
            widget.bind('<Button-1>', on_click)
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
    
    def create_goals_visualization(self, parent):
        """Create modern goals visualization panel"""
        viz_frame = tk.Frame(parent, bg=self.theme['bg_card'], relief='flat')
        viz_frame.grid(row=1, column=1, sticky='nsew', padx=(10, 0))
        
        # Header
        header_frame = tk.Frame(viz_frame, bg=self.theme['bg_secondary'], height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, text="GOALS OVERVIEW", 
                              font=('Roboto', 16, 'bold'), fg=self.theme['accent_cyan'], 
                              bg=self.theme['bg_secondary'])
        header_label.place(x=20, y=12)
        
        # Filter controls
        filter_frame = tk.Frame(header_frame, bg=self.theme['bg_secondary'])
        filter_frame.place(relx=1.0, rely=0.5, anchor='e', x=-20)
        
        # Status filter
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "Active", "Completed"], 
                                        state="readonly", font=('Roboto', 9), width=12)
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.filter_goals())
        self.status_filter.pack(side=tk.LEFT, padx=5)
        
        # Priority filter
        self.priority_filter = ttk.Combobox(filter_frame, values=["All", "High", "Medium", "Low"], 
                                          state="readonly", font=('Roboto', 9), width=12)
        self.priority_filter.set("All")
        self.priority_filter.bind('<<ComboboxSelected>>', lambda e: self.filter_goals())
        self.priority_filter.pack(side=tk.LEFT)
        
        # Goals table container
        table_container = tk.Frame(viz_frame, bg=self.theme['bg_card'])
        table_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        # Modern Treeview
        columns = ('ID', 'Goal', 'Type', 'Status', 'Progress', 'Priority', 'Deadline')
        self.goals_table = ttk.Treeview(table_container, columns=columns, show='headings', 
                                      style='Dark.Treeview', height=20)
        
        # Configure columns
        column_widths = {'ID': 50, 'Goal': 250, 'Type': 100, 'Status': 100, 
                        'Progress': 100, 'Priority': 80, 'Deadline': 120}
        
        for col in columns:
            self.goals_table.heading(col, text=col)
            self.goals_table.column(col, width=column_widths.get(col, 100), anchor='center' if col != 'Goal' else 'w')
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.goals_table.yview)
        h_scroll = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.goals_table.xview)
        
        self.goals_table.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack table and scrollbars
        self.goals_table.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.goals_table.bind('<<TreeviewSelect>>', self.on_goal_select)
        self.goals_table.bind('<Double-1>', self.on_goal_double_click)
        
        # Goal details panel
        self.create_goal_details_panel(viz_frame)
    
    def create_goal_details_panel(self, parent):
        """Create modern goal details panel"""
        # Details container at bottom
        self.details_container = tk.Frame(parent, bg=self.theme['bg_secondary'], height=200)
        self.details_container.pack(fill=tk.X, side=tk.BOTTOM)
        self.details_container.pack_propagate(False)
        
        # Details header
        details_header = tk.Frame(self.details_container, bg=self.theme['accent_purple'], height=30)
        details_header.pack(fill=tk.X)
        details_header.pack_propagate(False)
        
        details_title = tk.Label(details_header, text="GOAL DETAILS", 
                               font=('Roboto', 10, 'bold'), fg=self.theme['text_primary'], 
                               bg=self.theme['accent_purple'])
        details_title.place(x=20, y=5)
        
        # Details content
        self.details_content = tk.Frame(self.details_container, bg=self.theme['bg_secondary'])
        self.details_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Placeholder
        self.details_placeholder = tk.Label(self.details_content, 
                                           text="Select a goal to view details", 
                                           font=('Roboto', 12), fg=self.theme['text_muted'], 
                                           bg=self.theme['bg_secondary'])
        self.details_placeholder.pack(expand=True)
    
    def create_floating_actions(self):
        """Create floating action buttons"""
        # Floating container
        self.floating_frame = tk.Frame(self.root, bg=self.theme['bg_primary'])
        self.floating_frame.place(relx=0.95, rely=0.85, anchor='center')
        
        # Main floating button
        main_btn = tk.Button(self.floating_frame, text="+", 
                           font=('Roboto', 20, 'bold'), fg=self.theme['text_primary'], 
                           bg=self.theme['accent_cyan'], relief='flat', bd=0,
                           width=3, height=1, command=self.create_goal_dialog)
        main_btn.pack()
        
        # Hover effects
        def on_enter(event):
            main_btn.config(bg=self.theme['accent_green'])
        
        def on_leave(event):
            main_btn.config(bg=self.theme['accent_cyan'])
        
        main_btn.bind('<Enter>', on_enter)
        main_btn.bind('<Leave>', on_leave)
    
    def create_status_indicator(self):
        """Create animated status indicator"""
        self.status_frame = tk.Frame(self.root, bg=self.theme['bg_primary'])
        self.status_frame.place(relx=0.02, rely=0.95, anchor='w')
        
        self.status_label = tk.Label(self.status_frame, text="Ready", 
                                   font=('Roboto', 10), fg=self.theme['text_secondary'], 
                                   bg=self.theme['bg_primary'])
        self.status_label.pack()
    
    def refresh_dashboard(self):
        """Refresh all dashboard components"""
        self.load_goals_data()
        self.update_status("Dashboard refreshed")
    
    def load_goals_data(self):
        """Load and display goals data"""
        try:
            # Clear existing data
            for item in self.goals_table.get_children():
                self.goals_table.delete(item)
            
            # Get goals
            goals = self.gm.get_goals(self.current_user_id)
            
            for goal in goals:
                # Format data
                deadline_str = goal['deadline'].strftime('%Y-%m-%d') if goal['deadline'] else "No deadline"
                progress_str = f"{goal['progress_percentage']}%"
                
                # Color code progress
                progress_color = self.theme['accent_green'] if goal['progress_percentage'] >= 80 else \
                               self.theme['accent_orange'] if goal['progress_percentage'] >= 50 else \
                               self.theme['accent_red']
                
                # Insert with values
                item = self.goals_table.insert('', tk.END, values=(
                    goal['id'],
                    goal['title'],
                    goal['goal_type'].title(),
                    goal['status'],
                    progress_str,
                    goal['priority'],
                    deadline_str
                ))
                
                # Color code based on status
                if goal['status'] == 'Completed':
                    self.goals_table.set(item, 'Status', f"✓ {goal['status']}")
                elif goal['status'] == 'Active':
                    self.goals_table.set(item, 'Status', f"→ {goal['status']}")
            
        except Exception as e:
            print(f"Error loading goals: {e}")
            self.update_status("Error loading goals")
    
    def filter_goals(self):
        """Filter goals based on search and filters"""
        try:
            search_term = self.search_var.get().lower()
            status_filter = self.status_filter.get()
            priority_filter = self.priority_filter.get()
            
            # Clear table
            for item in self.goals_table.get_children():
                self.goals_table.delete(item)
            
            # Get filtered goals
            goals = self.gm.get_goals(self.current_user_id)
            
            # Apply filters
            filtered_goals = []
            for goal in goals:
                # Search filter
                if search_term and search_term not in goal['title'].lower():
                    if not goal['description'] or search_term not in goal['description'].lower():
                        continue
                
                # Status filter
                if status_filter != "All" and goal['status'] != status_filter:
                    continue
                
                # Priority filter
                if priority_filter != "All" and goal['priority'] != priority_filter:
                    continue
                
                filtered_goals.append(goal)
            
            # Display filtered goals
            for goal in filtered_goals:
                deadline_str = goal['deadline'].strftime('%Y-%m-%d') if goal['deadline'] else "No deadline"
                progress_str = f"{goal['progress_percentage']}%"
                
                item = self.goals_table.insert('', tk.END, values=(
                    goal['id'],
                    goal['title'],
                    goal['goal_type'].title(),
                    goal['status'],
                    progress_str,
                    goal['priority'],
                    deadline_str
                ))
            
            self.update_status(f"Showing {len(filtered_goals)} of {len(goals)} goals")
            
        except Exception as e:
            print(f"Error filtering goals: {e}")
    
    def on_goal_select(self, event):
        """Handle goal selection"""
        try:
            selection = self.goals_table.selection()
            if selection:
                item = self.goals_table.item(selection[0])
                goal_id = item['values'][0]
                self.selected_goal_id = goal_id
                self.show_goal_details(goal_id)
        except Exception as e:
            print(f"Error in goal selection: {e}")
    
    def on_goal_double_click(self, event):
        """Handle double-click to edit"""
        if self.selected_goal_id:
            self.edit_goal_dialog(self.selected_goal_id)
    
    def show_goal_details(self, goal_id):
        """Show goal details in bottom panel"""
        try:
            # Clear current details
            for widget in self.details_content.winfo_children():
                widget.destroy()
            
            goal = self.gm.get_goal_by_id(goal_id, self.current_user_id)
            if not goal:
                return
            
            # Details grid
            details_grid = tk.Frame(self.details_content, bg=self.theme['bg_secondary'])
            details_grid.pack(fill=tk.BOTH, expand=True)
            
            # Left side - Basic info
            left_frame = tk.Frame(details_grid, bg=self.theme['bg_secondary'])
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Goal title
            title_label = tk.Label(left_frame, text=goal['title'], 
                                 font=('Roboto', 16, 'bold'), fg=self.theme['text_primary'], 
                                 bg=self.theme['bg_secondary'])
            title_label.pack(anchor='w', pady=(0, 5))
            
            # Description
            if goal['description']:
                desc_label = tk.Label(left_frame, text=goal['description'], 
                                    font=('Roboto', 10), fg=self.theme['text_secondary'], 
                                    bg=self.theme['bg_secondary'], wraplength=400, justify='left')
                desc_label.pack(anchor='w', pady=(0, 10))
            
            # Info grid
            info_frame = tk.Frame(left_frame, bg=self.theme['bg_secondary'])
            info_frame.pack(anchor='w')
            
            info_data = [
                ("Type:", goal['goal_type'].title()),
                ("Priority:", goal['priority']),
                ("Status:", goal['status']),
                ("Created:", goal['created_at'].strftime('%Y-%m-%d') if goal['created_at'] else "N/A")
            ]
            
            for i, (label, value) in enumerate(info_data):
                row_frame = tk.Frame(info_frame, bg=self.theme['bg_secondary'])
                row_frame.grid(row=i, column=0, sticky='w', pady=2)
                
                tk.Label(row_frame, text=label, font=('Roboto', 10), 
                        fg=self.theme['text_muted'], bg=self.theme['bg_secondary']).pack(side=tk.LEFT)
                tk.Label(row_frame, text=value, font=('Roboto', 10, 'bold'), 
                        fg=self.theme['accent_cyan'], bg=self.theme['bg_secondary']).pack(side=tk.LEFT, padx=(10, 0))
            
            # Right side - Progress visualization
            right_frame = tk.Frame(details_grid, bg=self.theme['bg_secondary'])
            right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
            
            # Progress circle
            self.create_progress_circle(right_frame, goal['progress_percentage'])
            
            # Action buttons
            actions_frame = tk.Frame(right_frame, bg=self.theme['bg_secondary'])
            actions_frame.pack(pady=(20, 0))
            
            # Mini action buttons
            btn_configs = [
                ("Edit", lambda: self.edit_goal_dialog(goal_id), self.theme['accent_cyan']),
                ("Update", lambda: self.update_progress_dialog(goal_id), self.theme['accent_orange']),
                ("Complete", lambda: self.complete_goal_dialog(goal_id), self.theme['accent_green']),
                ("Delete", lambda: self.delete_goal_dialog(goal_id), self.theme['accent_red'])
            ]
            
            for text, command, color in btn_configs:
                btn = tk.Button(actions_frame, text=text, command=command,
                              font=('Roboto', 9, 'bold'), fg=self.theme['text_primary'], 
                              bg=color, relief='flat', bd=0, width=8)
                btn.pack(pady=2)
                
                # Hover effect
                def make_hover(button, original_color):
                    def on_enter(event):
                        button.config(bg=self.theme['text_primary'], fg=original_color)
                    def on_leave(event):
                        button.config(bg=original_color, fg=self.theme['text_primary'])
                    return on_enter, on_leave
                
                enter_func, leave_func = make_hover(btn, color)
                btn.bind('<Enter>', enter_func)
                btn.bind('<Leave>', leave_func)
            
        except Exception as e:
            print(f"Error showing goal details: {e}")
    
    def create_progress_circle(self, parent, progress):
        """Create circular progress indicator"""
        canvas = tk.Canvas(parent, width=120, height=120, bg=self.theme['bg_secondary'], 
                         highlightthickness=0)
        canvas.pack()
        
        # Background circle
        canvas.create_oval(10, 10, 110, 110, outline=self.theme['border'], width=3, fill='')
        
        # Progress arc
        if progress > 0:
            extent = (progress / 100) * 360
            canvas.create_arc(10, 10, 110, 110, start=90, extent=-extent, 
                            outline=self.theme['accent_cyan'], width=6, style='arc')
        
        # Progress text
        canvas.create_text(60, 60, text=f"{progress}%", font=('Roboto', 16, 'bold'), 
                         fill=self.theme['text_primary'])
        canvas.create_text(60, 80, text="Complete", font=('Roboto', 8), 
                         fill=self.theme['text_muted'])
    
    def create_goal_dialog(self):
        """Modern goal creation dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Goal - ZenGoals")
        dialog.geometry("600x700")
        dialog.configure(bg=self.theme['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        self.center_window(dialog, 600, 700)
        
        # Modern dialog header
        header_canvas = tk.Canvas(dialog, height=80, bg=self.theme['bg_primary'], highlightthickness=0)
        header_canvas.pack(fill=tk.X)
        
        # Gradient header
        for i in range(80):
            alpha = 1 - (i / 80)
            intensity = int(alpha * 50)
            color = f"#{intensity:02x}{intensity:02x}{intensity:02x}"
            header_canvas.create_line(0, i, 600, i, fill=color)
        
        header_canvas.create_text(30, 40, text="CREATE NEW GOAL", 
                                font=('Roboto', 20, 'bold'), fill=self.theme['accent_cyan'], anchor='w')
        
        # Form container
        form_frame = tk.Frame(dialog, bg=self.theme['bg_card'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Form fields with modern styling
        fields = {}
        
        # Title field
        self.create_modern_field(form_frame, "Goal Title", "title", fields, required=True)
        
        # Description field
        tk.Label(form_frame, text="Description", font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=self.theme['bg_card']).pack(anchor='w', pady=(20, 5))
        
        desc_container = tk.Frame(form_frame, bg=self.theme['bg_secondary'], relief='flat')
        desc_container.pack(fill=tk.X, pady=(0, 15))
        
        fields['description'] = tk.Text(desc_container, height=4, font=('Roboto', 11), 
                                      bg=self.theme['bg_secondary'], fg=self.theme['text_primary'], 
                                      insertbackground=self.theme['accent_cyan'], relief='flat', bd=0)
        fields['description'].pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Dropdowns in grid
        dropdown_frame = tk.Frame(form_frame, bg=self.theme['bg_card'])
        dropdown_frame.pack(fill=tk.X, pady=15)
        dropdown_frame.grid_columnconfigure(0, weight=1)
        dropdown_frame.grid_columnconfigure(1, weight=1)
        
        # Goal Type
        type_frame = tk.Frame(dropdown_frame, bg=self.theme['bg_card'])
        type_frame.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        tk.Label(type_frame, text="Goal Type", font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=self.theme['bg_card']).pack(anchor='w', pady=(0, 5))
        
        fields['goal_type'] = ttk.Combobox(type_frame, 
                                         values=["general", "fitness", "career", "learning", "financial", "health", "personal"],
                                         state="readonly", font=('Roboto', 10))
        fields['goal_type'].set("general")
        fields['goal_type'].pack(fill=tk.X)
        
        # Priority
        priority_frame = tk.Frame(dropdown_frame, bg=self.theme['bg_card'])
        priority_frame.grid(row=0, column=1, sticky='ew', padx=(10, 0))
        
        tk.Label(priority_frame, text="Priority", font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=self.theme['bg_card']).pack(anchor='w', pady=(0, 5))
        
        fields['priority'] = ttk.Combobox(priority_frame, values=["Low", "Medium", "High"],
                                        state="readonly", font=('Roboto', 10))
        fields['priority'].set("Medium")
        fields['priority'].pack(fill=tk.X)
        
        # Numeric fields in grid
        numeric_frame = tk.Frame(form_frame, bg=self.theme['bg_card'])
        numeric_frame.pack(fill=tk.X, pady=15)
        numeric_frame.grid_columnconfigure(0, weight=1)
        numeric_frame.grid_columnconfigure(1, weight=1)
        
        # Target Value
        self.create_modern_field(numeric_frame, "Target Value", "target_value", fields, 
                               parent_grid=(0, 0), grid_padx=(0, 10))
        
        # Deadline
        self.create_modern_field(numeric_frame, "Deadline (YYYY-MM-DD)", "deadline", fields, 
                               parent_grid=(0, 1), grid_padx=(10, 0))
        
        # Action buttons
        self.create_dialog_buttons(form_frame, fields, dialog, self.save_new_goal)
    
    def create_modern_field(self, parent, label, field_name, fields_dict, required=False, 
                          parent_grid=None, grid_padx=None):
        """Create modern input field with styling"""
        if parent_grid:
            container = tk.Frame(parent, bg=self.theme['bg_card'])
            container.grid(row=parent_grid[0], column=parent_grid[1], sticky='ew', 
                          padx=grid_padx or (0, 0))
        else:
            container = tk.Frame(parent, bg=self.theme['bg_card'])
            container.pack(fill=tk.X, pady=(0, 15))
        
        # Label
        label_text = f"{label}{'*' if required else ''}"
        tk.Label(container, text=label_text, font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=self.theme['bg_card']).pack(anchor='w', pady=(0, 5))
        
        # Entry with modern styling
        entry_container = tk.Frame(container, bg=self.theme['bg_secondary'], relief='flat')
        entry_container.pack(fill=tk.X)
        
        entry = tk.Entry(entry_container, font=('Roboto', 12), bg=self.theme['bg_secondary'], 
                        fg=self.theme['text_primary'], insertbackground=self.theme['accent_cyan'], 
                        relief='flat', bd=0)
        entry.pack(fill=tk.X, padx=10, pady=8)
        
        # Add focus effects
        def on_focus_in(event):
            entry_container.config(bg=self.theme['accent_cyan'])
        
        def on_focus_out(event):
            entry_container.config(bg=self.theme['bg_secondary'])
        
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        
        fields_dict[field_name] = entry
    
    def create_dialog_buttons(self, parent, fields, dialog, save_command):
        """Create modern dialog buttons"""
        btn_frame = tk.Frame(parent, bg=self.theme['bg_card'])
        btn_frame.pack(fill=tk.X, pady=(30, 0))
        
        # Save button
        save_btn = tk.Button(btn_frame, text="CREATE GOAL", 
                           command=lambda: save_command(fields, dialog),
                           font=('Roboto', 12, 'bold'), fg=self.theme['bg_primary'], 
                           bg=self.theme['accent_cyan'], relief='flat', bd=0,
                           padx=40, pady=12)
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Cancel button
        cancel_btn = tk.Button(btn_frame, text="CANCEL", command=dialog.destroy,
                             font=('Roboto', 12), fg=self.theme['text_primary'], 
                             bg=self.theme['bg_secondary'], relief='flat', bd=0,
                             padx=40, pady=12)
        cancel_btn.pack(side=tk.RIGHT)
        
        # Hover effects
        def save_hover_in(event):
            save_btn.config(bg=self.theme['accent_green'])
        def save_hover_out(event):
            save_btn.config(bg=self.theme['accent_cyan'])
        
        def cancel_hover_in(event):
            cancel_btn.config(bg=self.theme['accent_red'])
        def cancel_hover_out(event):
            cancel_btn.config(bg=self.theme['bg_secondary'])
        
        save_btn.bind('<Enter>', save_hover_in)
        save_btn.bind('<Leave>', save_hover_out)
        cancel_btn.bind('<Enter>', cancel_hover_in)
        cancel_btn.bind('<Leave>', cancel_hover_out)
    
    def save_new_goal(self, fields, dialog):
        """Save new goal from dialog"""
        try:
            title = fields['title'].get().strip()
            if not title:
                messagebox.showerror("Error", "Goal title is required")
                return
            
            description = fields['description'].get(1.0, tk.END).strip()
            goal_type = fields['goal_type'].get().lower()
            priority = fields['priority'].get()
            
            target_value = None
            if fields['target_value'].get().strip():
                try:
                    target_value = float(fields['target_value'].get())
                except ValueError:
                    messagebox.showerror("Error", "Target value must be a number")
                    return
            
            deadline = None
            if fields['deadline'].get().strip():
                try:
                    deadline = datetime.strptime(fields['deadline'].get(), '%Y-%m-%d').date()
                except ValueError:
                    messagebox.showerror("Error", "Deadline must be in YYYY-MM-DD format")
                    return
            
            goal_id = self.gm.create_goal(
                user_id=self.current_user_id,
                title=title,
                description=description if description else None,
                goal_type=goal_type,
                target_value=target_value,
                deadline=deadline,
                priority=priority
            )
            
            if goal_id:
                messagebox.showinfo("Success", f"Goal '{title}' created successfully!")
                dialog.destroy()
                self.refresh_dashboard()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create goal: {e}")
    
    def update_progress_dialog(self, goal_id=None):
        """Modern progress update dialog"""
        if not goal_id:
            if not self.selected_goal_id:
                messagebox.showwarning("Warning", "Please select a goal first")
                return
            goal_id = self.selected_goal_id
        
        goal = self.gm.get_goal_by_id(goal_id, self.current_user_id)
        if not goal:
            messagebox.showerror("Error", "Goal not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Progress - ZenGoals")
        dialog.geometry("500x400")
        dialog.configure(bg=self.theme['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        self.center_window(dialog, 500, 400)
        
        # Header
        header_frame = tk.Frame(dialog, bg=self.theme['accent_orange'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="UPDATE PROGRESS", 
                font=('Roboto', 16, 'bold'), fg=self.theme['text_primary'], 
                bg=self.theme['accent_orange']).place(x=20, y=15)
        
        # Form
        form_frame = tk.Frame(dialog, bg=self.theme['bg_card'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Goal info display
        tk.Label(form_frame, text=goal['title'], 
                font=('Roboto', 14, 'bold'), fg=self.theme['text_primary'], 
                bg=self.theme['bg_card']).pack(anchor='w', pady=(0, 10))
        
        tk.Label(form_frame, text=f"Current Progress: {goal['progress_percentage']}%", 
                font=('Roboto', 10), fg=self.theme['text_secondary'], 
                bg=self.theme['bg_card']).pack(anchor='w', pady=(0, 20))
        
        fields = {}
        
        # Current value field
        self.create_modern_field(form_frame, "New Progress Value", "current_value", fields, required=True)
        
        # Notes field
        tk.Label(form_frame, text="Notes", font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=self.theme['bg_card']).pack(anchor='w', pady=(10, 5))
        
        notes_container = tk.Frame(form_frame, bg=self.theme['bg_secondary'])
        notes_container.pack(fill=tk.X, pady=(0, 20))
        
        fields['notes'] = tk.Text(notes_container, height=3, font=('Roboto', 11), 
                                bg=self.theme['bg_secondary'], fg=self.theme['text_primary'], 
                                insertbackground=self.theme['accent_cyan'], relief='flat', bd=0)
        fields['notes'].pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pre-fill current value
        if goal['current_value']:
            fields['current_value'].insert(0, str(goal['current_value']))
        
        # Buttons
        def save_progress():
            try:
                current_value = fields['current_value'].get().strip()
                if not current_value:
                    messagebox.showerror("Error", "Progress value is required")
                    return
                
                try:
                    current_value = float(current_value)
                except ValueError:
                    messagebox.showerror("Error", "Progress value must be a number")
                    return
                
                notes = fields['notes'].get(1.0, tk.END).strip()
                
                if self.gm.update_goal_progress(goal_id, self.current_user_id, current_value, notes):
                    messagebox.showinfo("Success", "Progress updated successfully!")
                    dialog.destroy()
                    self.refresh_dashboard()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update progress: {e}")
        
        self.create_dialog_buttons(form_frame, fields, dialog, lambda f, d: save_progress())
    
    def complete_goal_dialog(self, goal_id=None):
        """Complete goal with confirmation"""
        if not goal_id:
            if not self.selected_goal_id:
                messagebox.showwarning("Warning", "Please select a goal first")
                return
            goal_id = self.selected_goal_id
        
        goal = self.gm.get_goal_by_id(goal_id, self.current_user_id)
        if not goal:
            messagebox.showerror("Error", "Goal not found")
            return
        
        if goal['status'] == 'Completed':
            messagebox.showinfo("Info", "This goal is already completed")
            return
        
        result = messagebox.askyesno("Complete Goal", 
                                   f"Mark '{goal['title']}' as completed?\n\nThis will set progress to 100%.")
        if result:
            if self.gm.complete_goal(goal_id, self.current_user_id):
                messagebox.showinfo("Success", "Goal completed! Congratulations!")
                self.refresh_dashboard()
    
    def delete_goal_dialog(self, goal_id=None):
        """Delete goal with confirmation"""
        if not goal_id:
            if not self.selected_goal_id:
                messagebox.showwarning("Warning", "Please select a goal first")
                return
            goal_id = self.selected_goal_id
        
        goal = self.gm.get_goal_by_id(goal_id, self.current_user_id)
        if not goal:
            messagebox.showerror("Error", "Goal not found")
            return
        
        result = messagebox.askyesno("Delete Goal", 
                                   f"Permanently delete '{goal['title']}'?\n\nThis action cannot be undone.")
        if result:
            if self.gm.delete_goal(goal_id, self.current_user_id):
                messagebox.showinfo("Success", "Goal deleted successfully")
                self.refresh_dashboard()
                self.clear_goal_details()
    
    def edit_goal_dialog(self, goal_id):
        """Edit existing goal"""
        goal = self.gm.get_goal_by_id(goal_id, self.current_user_id)
        if not goal:
            messagebox.showerror("Error", "Goal not found")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Goal - ZenGoals")
        dialog.geometry("600x700")
        dialog.configure(bg=self.theme['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        self.center_window(dialog, 600, 700)
        
        # Header
        header_frame = tk.Frame(dialog, bg=self.theme['accent_purple'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="EDIT GOAL", 
                font=('Roboto', 16, 'bold'), fg=self.theme['text_primary'], 
                bg=self.theme['accent_purple']).place(x=20, y=15)
        
        # Form with pre-filled data
        form_frame = tk.Frame(dialog, bg=self.theme['bg_card'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        fields = {}
        
        # Pre-fill all fields
        self.create_modern_field(form_frame, "Goal Title", "title", fields, required=True)
        fields['title'].insert(0, goal['title'])
        
        # Description
        tk.Label(form_frame, text="Description", font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=self.theme['bg_card']).pack(anchor='w', pady=(20, 5))
        
        desc_container = tk.Frame(form_frame, bg=self.theme['bg_secondary'])
        desc_container.pack(fill=tk.X, pady=(0, 15))
        
        fields['description'] = tk.Text(desc_container, height=4, font=('Roboto', 11), 
                                      bg=self.theme['bg_secondary'], fg=self.theme['text_primary'], 
                                      insertbackground=self.theme['accent_cyan'], relief='flat', bd=0)
        fields['description'].pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if goal['description']:
            fields['description'].insert(1.0, goal['description'])
        
        # Dropdowns
        dropdown_frame = tk.Frame(form_frame, bg=self.theme['bg_card'])
        dropdown_frame.pack(fill=tk.X, pady=15)
        dropdown_frame.grid_columnconfigure(0, weight=1)
        dropdown_frame.grid_columnconfigure(1, weight=1)
        
        # Goal Type
        type_frame = tk.Frame(dropdown_frame, bg=self.theme['bg_card'])
        type_frame.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        tk.Label(type_frame, text="Goal Type", font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=self.theme['bg_card']).pack(anchor='w', pady=(0, 5))
        
        fields['goal_type'] = ttk.Combobox(type_frame, 
                                         values=["general", "fitness", "career", "learning", "financial", "health", "personal"],
                                         state="readonly", font=('Roboto', 10))
        fields['goal_type'].set(goal['goal_type'])
        fields['goal_type'].pack(fill=tk.X)
        
        # Priority
        priority_frame = tk.Frame(dropdown_frame, bg=self.theme['bg_card'])
        priority_frame.grid(row=0, column=1, sticky='ew', padx=(10, 0))
        
        tk.Label(priority_frame, text="Priority", font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=self.theme['bg_card']).pack(anchor='w', pady=(0, 5))
        
        fields['priority'] = ttk.Combobox(priority_frame, values=["Low", "Medium", "High"],
                                        state="readonly", font=('Roboto', 10))
        fields['priority'].set(goal['priority'])
        fields['priority'].pack(fill=tk.X)
        
        # Numeric fields
        numeric_frame = tk.Frame(form_frame, bg=self.theme['bg_card'])
        numeric_frame.pack(fill=tk.X, pady=15)
        numeric_frame.grid_columnconfigure(0, weight=1)
        numeric_frame.grid_columnconfigure(1, weight=1)
        
        self.create_modern_field(numeric_frame, "Target Value", "target_value", fields, 
                               parent_grid=(0, 0), grid_padx=(0, 10))
        if goal['target_value']:
            fields['target_value'].insert(0, str(goal['target_value']))
        
        self.create_modern_field(numeric_frame, "Deadline (YYYY-MM-DD)", "deadline", fields, 
                               parent_grid=(0, 1), grid_padx=(10, 0))
        if goal['deadline']:
            fields['deadline'].insert(0, goal['deadline'].strftime('%Y-%m-%d'))
        
        # Save function
        def save_changes():
            try:
                title = fields['title'].get().strip()
                if not title:
                    messagebox.showerror("Error", "Goal title is required")
                    return
                
                description = fields['description'].get(1.0, tk.END).strip()
                goal_type = fields['goal_type'].get()
                priority = fields['priority'].get()
                
                target_value = None
                if fields['target_value'].get().strip():
                    try:
                        target_value = float(fields['target_value'].get())
                    except ValueError:
                        messagebox.showerror("Error", "Target value must be a number")
                        return
                
                deadline = None
                if fields['deadline'].get().strip():
                    try:
                        deadline = datetime.strptime(fields['deadline'].get(), '%Y-%m-%d').date()
                    except ValueError:
                        messagebox.showerror("Error", "Deadline must be in YYYY-MM-DD format")
                        return
                
                # Update goal
                update_query = """
                UPDATE goals 
                SET title = %s, description = %s, goal_type = %s, target_value = %s, 
                    deadline = %s, priority = %s, updated_at = NOW()
                WHERE id = %s AND user_id = %s
                """
                params = (title, description, goal_type, target_value, deadline, priority, goal_id, self.current_user_id)
                
                result = self.gm.db.execute_query(update_query, params)
                
                if result:
                    messagebox.showinfo("Success", "Goal updated successfully!")
                    dialog.destroy()
                    self.refresh_dashboard()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update goal: {e}")
        
        # Custom save button for edit
        btn_frame = tk.Frame(form_frame, bg=self.theme['bg_card'])
        btn_frame.pack(fill=tk.X, pady=(30, 0))
        
        save_btn = tk.Button(btn_frame, text="SAVE CHANGES", command=save_changes,
                           font=('Roboto', 12, 'bold'), fg=self.theme['bg_primary'], 
                           bg=self.theme['accent_purple'], relief='flat', bd=0,
                           padx=40, pady=12)
        save_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = tk.Button(btn_frame, text="CANCEL", command=dialog.destroy,
                             font=('Roboto', 12), fg=self.theme['text_primary'], 
                             bg=self.theme['bg_secondary'], relief='flat', bd=0,
                             padx=40, pady=12)
        cancel_btn.pack(side=tk.RIGHT)
    
    def show_analytics(self):
        """Show detailed analytics in modern design"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Goal Analytics - ZenGoals")
        dialog.geometry("900x700")
        dialog.configure(bg=self.theme['bg_primary'])
        dialog.transient(self.root)
        
        self.center_window(dialog, 900, 700)
        
        # Animated header
        header_canvas = tk.Canvas(dialog, height=80, bg=self.theme['bg_primary'], highlightthickness=0)
        header_canvas.pack(fill=tk.X)
        
        # Gradient
        for i in range(80):
            alpha = 1 - (i / 80)
            intensity = int(alpha * 60)
            color = f"#{intensity:02x}{intensity:02x}{intensity:02x}"
            header_canvas.create_line(0, i, 900, i, fill=color)
        
        header_canvas.create_text(30, 40, text="ANALYTICS DASHBOARD", 
                                font=('Roboto', 20, 'bold'), fill=self.theme['accent_purple'], anchor='w')
        
        # Analytics content
        content_frame = tk.Frame(dialog, bg=self.theme['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Get comprehensive stats
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        goals = self.gm.get_goals(self.current_user_id)
        
        # Analytics cards grid
        analytics_grid = tk.Frame(content_frame, bg=self.theme['bg_primary'])
        analytics_grid.pack(fill=tk.X, pady=(0, 20))
        
        # Performance metrics
        self.create_analytics_card(analytics_grid, "PERFORMANCE METRICS", [
            ("Total Goals Created", stats.get('total_goals', 0)),
            ("Goals Completed", stats.get('completed_goals', 0)),
            ("Success Rate", f"{stats.get('completion_rate', 0):.1f}%"),
            ("Average Progress", f"{stats.get('average_progress', 0):.1f}%")
        ], self.theme['accent_cyan'], 0)
        
        # Goal types breakdown
        if goals:
            type_stats = {}
            for goal in goals:
                goal_type = goal['goal_type'].title()
                type_stats[goal_type] = type_stats.get(goal_type, 0) + 1
            
            type_data = [(k, v) for k, v in type_stats.items()]
            self.create_analytics_card(analytics_grid, "GOALS BY TYPE", type_data, 
                                     self.theme['accent_green'], 1)
        
        # Priority breakdown
        if goals:
            priority_stats = {}
            for goal in goals:
                priority = goal['priority']
                priority_stats[priority] = priority_stats.get(priority, 0) + 1
            
            priority_data = [(k, v) for k, v in priority_stats.items()]
            self.create_analytics_card(analytics_grid, "PRIORITY DISTRIBUTION", priority_data, 
                                     self.theme['accent_orange'], 2)
        
        # Recent activity
        recent_goals = goals[:5] if goals else []
        recent_data = []
        for goal in recent_goals:
            status_icon = "✓" if goal['status'] == 'Completed' else "→"
            recent_data.append((f"{status_icon} {goal['title']}", f"{goal['progress_percentage']}%"))
        
        if recent_data:
            self.create_analytics_card(content_frame, "RECENT ACTIVITY", recent_data, 
                                     self.theme['accent_purple'], None, full_width=True)
        
        # Close button
        close_btn = tk.Button(content_frame, text="CLOSE", command=dialog.destroy,
                            font=('Roboto', 12, 'bold'), fg=self.theme['text_primary'], 
                            bg=self.theme['accent_red'], relief='flat', bd=0,
                            padx=40, pady=12)
        close_btn.pack(pady=(20, 0))
    
    def create_analytics_card(self, parent, title, data, color, column=None, full_width=False):
        """Create analytics card"""
        if full_width:
            card_container = tk.Frame(parent, bg=self.theme['bg_card'], relief='flat')
            card_container.pack(fill=tk.X, pady=10)
        else:
            card_container = tk.Frame(parent, bg=self.theme['bg_card'], relief='flat')
            card_container.grid(row=0, column=column, sticky='ew', padx=10, pady=10)
            parent.grid_columnconfigure(column, weight=1)
        
        # Card header
        header = tk.Frame(card_container, bg=color, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=title, font=('Roboto', 12, 'bold'), 
                fg=self.theme['text_primary'], bg=color).place(x=15, y=10)
        
        # Card content
        content = tk.Frame(card_container, bg=self.theme['bg_card'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        for label, value in data:
            row = tk.Frame(content, bg=self.theme['bg_card'])
            row.pack(fill=tk.X, pady=3)
            
            tk.Label(row, text=str(label), font=('Roboto', 10), 
                    fg=self.theme['text_secondary'], bg=self.theme['bg_card']).pack(side=tk.LEFT)
            tk.Label(row, text=str(value), font=('Roboto', 10, 'bold'), 
                    fg=color, bg=self.theme['bg_card']).pack(side=tk.RIGHT)
    
    def clear_goal_details(self):
        """Clear goal details panel"""
        for widget in self.details_content.winfo_children():
            widget.destroy()
        
        self.details_placeholder = tk.Label(self.details_content, 
                                           text="Select a goal to view details", 
                                           font=('Roboto', 12), fg=self.theme['text_muted'], 
                                           bg=self.theme['bg_secondary'])
        self.details_placeholder.pack(expand=True)
        
        self.selected_goal_id = None
    
    def center_window(self, window, width, height):
        """Center a window on screen"""
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def update_status(self, message):
        """Update status indicator"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
            # Auto-clear after 3 seconds
            self.root.after(3000, lambda: self.status_label.config(text="Ready"))
    
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Application terminated by user")
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            self.on_closing()


def main():
    """Main function to run the application"""
    try:
        print("Starting ZenGoals - Modern Goal Tracker...")
        print("Unique Dark Theme with Neon Accents")
        print("=" * 50)
        
        app = UniqueGoalsManagerGUI()
        app.run()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        messagebox.showerror("Application Error", f"Failed to start application: {e}")


if __name__ == "__main__":
    main()
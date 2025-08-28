import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from db_connect import connect_db as shared_connect_db

class GoalsManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect_db(self):
        """Database connection establish kore"""
        conn = shared_connect_db()
        if not conn:
            # Bangla friendly message — DB connection failed
            messagebox.showerror("ডাটাবেস ত্রুটি", "ডাটাবেসে সংযোগ করা যাচ্ছেনা। কনফিগারেশন পরীক্ষা করুন।")
            return False
        self.connection = conn
        try:
            # prefer dictionary cursor for easier access
            self.cursor = self.connection.cursor(dictionary=True)
        except Exception:
            # fallback to normal cursor
            self.cursor = self.connection.cursor()
        return True
    
    def disconnect_db(self):
        """Database connection close kore"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def create_goal(self, user_id: int, title: str, description: str = None, 
                   goal_type: str = "general", target_value: float = None, 
                   deadline: str = None, priority: str = "Medium") -> int:
        """Notun goal create kore"""
        try:
            query = """
                INSERT INTO goals (user_id, title, description, goal_type, 
                                 target_value, current_value, progress_percentage, 
                                 deadline, status, priority)
                VALUES (%s, %s, %s, %s, %s, 0, 0, %s, 'Active', %s)
            """
            values = (user_id, title, description, goal_type, target_value, deadline, priority)
            self.cursor.execute(query, values)
            self.connection.commit()
            
            return self.cursor.lastrowid
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to create goal: {err}")
            return None
    
    def get_goals(self, user_id: int, status: str = None) -> List[Dict]:
        """User er sob goals get kore"""
        try:
            if status:
                query = "SELECT * FROM goals WHERE user_id = %s AND status = %s ORDER BY created_at DESC"
                self.cursor.execute(query, (user_id, status))
            else:
                query = "SELECT * FROM goals WHERE user_id = %s ORDER BY created_at DESC"
                self.cursor.execute(query, (user_id,))
            
            return self.cursor.fetchall()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to get goals: {err}")
            return []
    
    def get_goal_by_id(self, goal_id: int, user_id: int) -> Dict:
        """Specific goal get kore"""
        try:
            query = "SELECT * FROM goals WHERE id = %s AND user_id = %s"
            self.cursor.execute(query, (goal_id, user_id))
            return self.cursor.fetchone()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to get goal: {err}")
            return None
    
    def update_goal_progress(self, goal_id: int, user_id: int, current_value: float, 
                           notes: str = None) -> bool:
        """Goal er progress update kore"""
        try:
            goal = self.get_goal_by_id(goal_id, user_id)
            if not goal:
                return False
            
            target_value = goal['target_value']
            if target_value and target_value > 0:
                progress_percentage = min(100, int((current_value / target_value) * 100))
            else:
                progress_percentage = 0
            
            update_query = """
                UPDATE goals 
                SET current_value = %s, progress_percentage = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
            """
            self.cursor.execute(update_query, (current_value, progress_percentage, goal_id, user_id))
            
            progress_query = """
                INSERT INTO goal_progress (goal_id, user_id, progress_percentage, notes)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(progress_query, (goal_id, user_id, progress_percentage, notes))
            
            self.connection.commit()
            
            if progress_percentage >= 100:
                self.complete_goal(goal_id, user_id)
            
            return True
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to update progress: {err}")
            return False
    
    def complete_goal(self, goal_id: int, user_id: int) -> bool:
        """Goal complete kore"""
        try:
            query = """
                UPDATE goals 
                SET status = 'Completed', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
            """
            self.cursor.execute(query, (goal_id, user_id))
            self.connection.commit()
            return True
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to complete goal: {err}")
            return False
    
    def delete_goal(self, goal_id: int, user_id: int) -> bool:
        """Goal delete kore"""
        try:
            self.cursor.execute("DELETE FROM goal_progress WHERE goal_id = %s", (goal_id,))
            query = "DELETE FROM goals WHERE id = %s AND user_id = %s"
            self.cursor.execute(query, (goal_id, user_id))
            self.connection.commit()
            
            return self.cursor.rowcount > 0
                
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to delete goal: {err}")
            return False
    
    def get_user_goal_stats(self, user_id: int) -> Dict:
        """User er goal statistics get kore"""
        try:
            self.cursor.execute("SELECT COUNT(*) as total FROM goals WHERE user_id = %s", (user_id,))
            total_goals = self.cursor.fetchone()['total']
            
            self.cursor.execute(
                "SELECT COUNT(*) as completed FROM goals WHERE user_id = %s AND status = 'Completed'", 
                (user_id,)
            )
            completed_goals = self.cursor.fetchone()['completed']
            
            self.cursor.execute(
                "SELECT COUNT(*) as active FROM goals WHERE user_id = %s AND status = 'Active'", 
                (user_id,)
            )
            active_goals = self.cursor.fetchone()['active']
            
            self.cursor.execute(
                "SELECT AVG(progress_percentage) as avg_progress FROM goals WHERE user_id = %s AND status = 'Active'", 
                (user_id,)
            )
            avg_progress = self.cursor.fetchone()['avg_progress'] or 0
            
            return {
                'total_goals': total_goals,
                'completed_goals': completed_goals,
                'active_goals': active_goals,
                'completion_rate': (completed_goals / total_goals * 100) if total_goals > 0 else 0,
                'average_progress': round(float(avg_progress), 2)
            }
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to get statistics: {err}")
            return {}


class GoalsManagerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 Goals Management System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Database manager
        self.gm = GoalsManager()
        if not self.gm.connect_db():
            return
        
        # Current user (in real app, this would come from login)
        self.current_user_id = 1
        
        # Configure styles
        self.setup_styles()
        
        # Create GUI
        self.create_widgets()
        
        # Load initial data
        self.refresh_goals_list()
    
    def setup_styles(self):
        """GUI styles setup kore"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'), foreground='#34495e')
        style.configure('Success.TLabel', foreground='#27ae60')
        style.configure('Warning.TLabel', foreground='#e74c3c')
        style.configure('Custom.TButton', padding=10)
    
    def create_widgets(self):
        """Main GUI widgets create kore"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎯 Goals Management System", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Controls
        self.create_control_panel(main_frame)
        
        # Right panel - Goals list
        self.create_goals_panel(main_frame)
        
        # Bottom panel - Statistics
        self.create_stats_panel(main_frame)
    
    def create_control_panel(self, parent):
        """Left side control panel create kore"""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="15")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Buttons
        buttons = [
            ("➕ Create New Goal", self.create_goal_dialog),
            ("📊 Update Progress", self.update_progress_dialog),
            ("✅ Complete Goal", self.complete_goal_dialog),
            ("🗑️ Delete Goal", self.delete_goal_dialog),
            ("🔄 Refresh List", self.refresh_goals_list),
            ("📈 View Statistics", self.show_statistics)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(control_frame, text=text, command=command, style='Custom.TButton')
            btn.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=5)
            control_frame.columnconfigure(0, weight=1)
        
        # Filter options
        ttk.Separator(control_frame, orient='horizontal').grid(row=len(buttons), column=0, sticky=(tk.W, tk.E), pady=20)
        
        ttk.Label(control_frame, text="Filter by Status:", style='Heading.TLabel').grid(row=len(buttons)+1, column=0, sticky=tk.W)
        
        self.status_filter = ttk.Combobox(control_frame, values=["All", "Active", "Completed"], state="readonly")
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_goals_list())
        self.status_filter.grid(row=len(buttons)+2, column=0, sticky=(tk.W, tk.E), pady=5)
    
    def create_goals_panel(self, parent):
        """Right side goals list panel create kore"""
        goals_frame = ttk.LabelFrame(parent, text="Goals List", padding="15")
        goals_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        goals_frame.columnconfigure(0, weight=1)
        goals_frame.rowconfigure(0, weight=1)
        
        # Treeview for goals
        columns = ('ID', 'Title', 'Type', 'Progress', 'Status', 'Priority', 'Deadline')
        self.goals_tree = ttk.Treeview(goals_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        column_widths = {'ID': 50, 'Title': 200, 'Type': 80, 'Progress': 80, 'Status': 80, 'Priority': 80, 'Deadline': 100}
        for col in columns:
            self.goals_tree.heading(col, text=col)
            self.goals_tree.column(col, width=column_widths.get(col, 100))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(goals_frame, orient=tk.VERTICAL, command=self.goals_tree.yview)
        h_scrollbar = ttk.Scrollbar(goals_frame, orient=tk.HORIZONTAL, command=self.goals_tree.xview)
        self.goals_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.goals_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Double click to view details
        self.goals_tree.bind('<Double-1>', self.show_goal_details)
    
    def create_stats_panel(self, parent):
        """Bottom statistics panel create kore"""
        self.stats_frame = ttk.LabelFrame(parent, text="Quick Statistics", padding="15")
        self.stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Stats labels will be created dynamically
        self.stats_labels = {}
    
    def refresh_goals_list(self):
        """Goals list refresh kore"""
        # Clear existing items
        for item in self.goals_tree.get_children():
            self.goals_tree.delete(item)
        
        # Get filter value
        status_filter = self.status_filter.get()
        status = None if status_filter == "All" else status_filter
        
        # Get goals from database
        goals = self.gm.get_goals(self.current_user_id, status)
        
        # Populate treeview
        for goal in goals:
            values = (
                goal['id'],
                goal['title'][:30] + "..." if len(goal['title']) > 30 else goal['title'],
                goal['goal_type'],
                f"{goal['progress_percentage']}%",
                goal['status'],
                goal['priority'],
                str(goal['deadline']) if goal['deadline'] else "No deadline"
            )
            
            # Color coding based on status and progress
            tags = []
            if goal['status'] == 'Completed':
                tags.append('completed')
            elif goal['progress_percentage'] >= 75:
                tags.append('high_progress')
            elif goal['progress_percentage'] >= 25:
                tags.append('medium_progress')
            else:
                tags.append('low_progress')
            
            self.goals_tree.insert('', tk.END, values=values, tags=tags)
        
        # Configure tags
        self.goals_tree.tag_configure('completed', background='#d5edda')
        self.goals_tree.tag_configure('high_progress', background='#fff3cd')
        self.goals_tree.tag_configure('medium_progress', background='#cce5ff')
        self.goals_tree.tag_configure('low_progress', background='#f8d7da')
        
        # Update statistics
        self.update_statistics()
    
    def update_statistics(self):
        """Statistics update kore"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        # Clear existing labels
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        if not stats:
            return
        
        # Create stats labels
        stats_info = [
            (f"Total Goals: {stats['total_goals']}", 'Heading.TLabel'),
            (f"Active: {stats['active_goals']}", 'Custom.TLabel'),
            (f"Completed: {stats['completed_goals']}", 'Success.TLabel'),
            (f"Completion Rate: {stats['completion_rate']:.1f}%", 'Success.TLabel'),
            (f"Average Progress: {stats['average_progress']}%", 'Custom.TLabel')
        ]
        
        for i, (text, style) in enumerate(stats_info):
            label = ttk.Label(self.stats_frame, text=text, style=style)
            label.grid(row=0, column=i, padx=20)
    
    def create_goal_dialog(self):
        """Goal create korar dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Goal")
        dialog.geometry("500x400")
        dialog.configure(bg='#f0f0f0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        fields = {}
        
        # Title
        ttk.Label(frame, text="Title:*", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        fields['title'] = ttk.Entry(frame, width=40)
        fields['title'].grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Description
        ttk.Label(frame, text="Description:", style='Heading.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        fields['description'] = tk.Text(frame, width=35, height=4)
        fields['description'].grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Goal Type
        ttk.Label(frame, text="Type:", style='Heading.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        fields['goal_type'] = ttk.Combobox(frame, values=["general", "fitness", "career", "personal", "financial"], state="readonly")
        fields['goal_type'].set("general")
        fields['goal_type'].grid(row=2, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Target Value
        ttk.Label(frame, text="Target Value:", style='Heading.TLabel').grid(row=3, column=0, sticky=tk.W, pady=5)
        fields['target_value'] = ttk.Entry(frame, width=20)
        fields['target_value'].grid(row=3, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Priority
        ttk.Label(frame, text="Priority:", style='Heading.TLabel').grid(row=4, column=0, sticky=tk.W, pady=5)
        fields['priority'] = ttk.Combobox(frame, values=["Low", "Medium", "High"], state="readonly")
        fields['priority'].set("Medium")
        fields['priority'].grid(row=4, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Deadline
        ttk.Label(frame, text="Deadline (YYYY-MM-DD):", style='Heading.TLabel').grid(row=5, column=0, sticky=tk.W, pady=5)
        fields['deadline'] = ttk.Entry(frame, width=20)
        fields['deadline'].grid(row=5, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        def create_goal():
            title = fields['title'].get().strip()
            if not title:
                messagebox.showerror("Error", "Title is required!")
                return
            
            description = fields['description'].get(1.0, tk.END).strip() or None
            goal_type = fields['goal_type'].get()
            
            try:
                target_value = float(fields['target_value'].get()) if fields['target_value'].get().strip() else None
            except ValueError:
                target_value = None
            
            priority = fields['priority'].get()
            deadline = fields['deadline'].get().strip() or None
            
            goal_id = self.gm.create_goal(self.current_user_id, title, description, goal_type, target_value, deadline, priority)
            
            if goal_id:
                messagebox.showinfo("Success", f"Goal created successfully! ID: {goal_id}")
                dialog.destroy()
                self.refresh_goals_list()
            else:
                messagebox.showerror("Error", "Failed to create goal!")
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Create Goal", command=create_goal).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def update_progress_dialog(self):
        """Progress update korar dialog"""
        selected = self.goals_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a goal first!")
            return
        
        goal_id = self.goals_tree.item(selected[0])['values'][0]
        goal = self.gm.get_goal_by_id(goal_id, self.current_user_id)
        
        if not goal:
            messagebox.showerror("Error", "Goal not found!")
            return
        
        if goal['status'] == 'Completed':
            messagebox.showinfo("Info", "Goal is already completed!")
            return
        
        # Simple dialog for progress update
        current_value = simpledialog.askfloat(
            "Update Progress",
            f"Goal: {goal['title']}\nTarget: {goal['target_value']}\nCurrent: {goal['current_value']}\n\nEnter new current value:",
            initialvalue=goal['current_value']
        )
        
        if current_value is not None:
            notes = simpledialog.askstring("Update Progress", "Add notes (optional):")
            
            if self.gm.update_goal_progress(goal_id, self.current_user_id, current_value, notes):
                messagebox.showinfo("Success", "Progress updated successfully!")
                self.refresh_goals_list()
    
    def complete_goal_dialog(self):
        """Goal complete korar dialog"""
        selected = self.goals_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a goal first!")
            return
        
        goal_id = self.goals_tree.item(selected[0])['values'][0]
        goal_title = self.goals_tree.item(selected[0])['values'][1]
        
        if messagebox.askyesno("Confirm", f"Mark '{goal_title}' as completed?"):
            if self.gm.complete_goal(goal_id, self.current_user_id):
                messagebox.showinfo("Success", "Goal completed! 🎉")
                self.refresh_goals_list()
    
    def delete_goal_dialog(self):
        """Goal delete korar dialog"""
        selected = self.goals_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a goal first!")
            return
        
        goal_id = self.goals_tree.item(selected[0])['values'][0]
        goal_title = self.goals_tree.item(selected[0])['values'][1]
        
        if messagebox.askyesno("Confirm", f"Delete '{goal_title}'? This action cannot be undone!"):
            if self.gm.delete_goal(goal_id, self.current_user_id):
                messagebox.showinfo("Success", "Goal deleted successfully!")
                self.refresh_goals_list()
    
    def show_goal_details(self, event):
        """Goal er details show kore"""
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
        details_window.geometry("600x500")
        details_window.configure(bg='#f0f0f0')
        
        frame = ttk.Frame(details_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Goal information
        info_text = f"""
🎯 Title: {goal['title']}
📝 Description: {goal['description'] or 'No description'}
🏷️  Type: {goal['goal_type']}
📊 Progress: {goal['progress_percentage']}%
🎯 Target: {goal['current_value']}/{goal['target_value'] or 'No target'}
⚡ Priority: {goal['priority']}
📅 Status: {goal['status']}
⏰ Deadline: {goal['deadline'] or 'No deadline'}
📅 Created: {goal['created_at']}
📅 Updated: {goal['updated_at']}
        """
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=('Arial', 11))
        text_widget.insert(1.0, info_text.strip())
        text_widget.configure(state='disabled')
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        ttk.Label(frame, text=f"Progress: {goal['progress_percentage']}%", style='Heading.TLabel').pack(pady=(10, 5))
        progress_bar = ttk.Progressbar(frame, length=400, mode='determinate')
        progress_bar['value'] = goal['progress_percentage']
        progress_bar.pack(pady=(0, 10))
    
    def show_statistics(self):
        """Detailed statistics show kore"""
        stats = self.gm.get_user_goal_stats(self.current_user_id)
        
        if not stats:
            messagebox.showinfo("Statistics", "No statistics available!")
            return
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Goal Statistics")
        stats_window.geometry("400x300")
        stats_window.configure(bg='#f0f0f0')
        
        frame = ttk.Frame(stats_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="📈 Goal Statistics", style='Title.TLabel').pack(pady=(0, 20))
        
        stats_info = f"""
📊 Total Goals: {stats['total_goals']}
✅ Completed Goals: {stats['completed_goals']}
🔄 Active Goals: {stats['active_goals']}
📈 Completion Rate: {stats['completion_rate']:.1f}%
⚡ Average Progress: {stats['average_progress']}%
        """
        
        stats_label = ttk.Label(frame, text=stats_info.strip(), font=('Arial', 12))
        stats_label.pack()
    
    def run(self):
        """GUI run kore"""
        try:
            self.root.mainloop()
        finally:
            self.gm.disconnect_db()


def main():
    """Main function"""
    try:
        app = GoalsManagerGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main()
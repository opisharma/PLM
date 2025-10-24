from tkinter import *
from tkinter import messagebox, ttk
import sys
import os
import subprocess
from datetime import datetime
from tasks_ui import show_tasks as tasks_show_ui
from expenses_ui import show_expenses as expenses_show_ui
from goals_ui import show_goals as goals_show_ui
from medications_ui import show_medications as medications_show_ui

# Prefer shared DB connector from db_connect; fallback to local if unavailable
try:
    from db_connect import connect_db  # type: ignore
except Exception:
    # Fallback: local connector using mysql.connector
    import mysql.connector  # type: ignore

    def connect_db():
        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="life_manger",
            )
            print("✅ Connected to MySQL database successfully!")
            return db
        except Exception as err:
            print("❌ Failed to connect:", err)
            return None

# === Global Variables (No login required) ===
current_user = "Admin"  # Default user
root = None
content_frame = None

# === Utilities ===
def center_window(win: Tk, width: int | None = None, height: int | None = None):
    """Center the given window on screen, optionally forcing size first."""
    try:
        win.update_idletasks()
        if width and height:
            win.geometry(f"{width}x{height}")
        w = win.winfo_width()
        h = win.winfo_height()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

def parse_cli_user_id() -> str | None:
    for arg in sys.argv[1:]:
        if arg.startswith("--user_id="):
            return arg.split("=", 1)[1] or None
    return None

def resolve_user_name(user_id: str) -> str | None:
    """Try to load user's display name from DB; return None on failure."""
    try:
        db = connect_db()
        if not db:
            return None
        cur = db.cursor()
        # Try common columns
        cur.execute("SELECT name FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        cur.close()
        try:
            db.close()
        except Exception:
            pass
        if row and row[0]:
            return str(row[0])
    except Exception:
        return None
    return None

def init_styles():
    style = ttk.Style()
    # On some Linux themes, set theme explicitly for consistency
    try:
        if sys.platform.startswith("linux") and style.theme_use() == "clam":
            style.theme_use("clam")
    except Exception:
        pass
    style.configure("Custom.Treeview.Heading", font=("Segoe UI", 11, "bold"))
    style.configure("Custom.Treeview", font=("Segoe UI", 10))

# === Clear content before loading next ===
def clear_frame():
    for widget in content_frame.winfo_children():
        widget.destroy()

# === Show Dashboard (Main Entry Point) ===
def show_dashboard():
    clear_frame()

    # Header with gradient-like effect
    header_frame = Frame(content_frame, bg="#2c3e50", height=80)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)

    Label(header_frame, text="🧠 Life Manager Dashboard", font=("Segoe UI", 28, "bold"),
          bg="#2c3e50", fg="#ffffff").pack(side=LEFT, padx=20)

    # Clock and Date
    clock_frame = Frame(header_frame, bg="#2c3e50")
    clock_frame.pack(side=RIGHT, padx=20, pady=10)

    time_label = Label(clock_frame, font=("Segoe UI", 22, "bold"), bg="#2c3e50", fg="#ffffff")
    time_label.pack()
    date_label = Label(clock_frame, font=("Segoe UI", 12), bg="#2c3e50", fg="#ecf0f1")
    date_label.pack()

    def update_clock():
        now = datetime.now()
        time_label.config(text=now.strftime("%H:%M:%S"))
        date_label.config(text=now.strftime("%A, %B %d, %Y"))
        header_frame.after(1000, update_clock)

    update_clock()

    # Quick Stats
    stats_frame = Frame(content_frame, bg="#f8f9fc")
    stats_frame.pack(fill=X, padx=40, pady=(0, 10))

    def create_stat_item(parent, label, value, color):
        frame = Frame(parent, bg=color, relief="raised", bd=1)
        Label(frame, text=label, font=("Segoe UI", 11, "bold"), bg=color, fg="white").pack(padx=10, pady=(5,0))
        Label(frame, text=value, font=("Segoe UI", 18, "bold"), bg=color, fg="white").pack(padx=10, pady=(0,5))
        return frame

    # Fetch stats from DB
    try:
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status != 'Completed'")
            pending_tasks = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM medications WHERE end_date >= CURDATE()")
            active_meds = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM goals WHERE status != 'Achieved'")
            active_goals = cursor.fetchone()[0]
            conn.close()
        else:
            pending_tasks, active_meds, active_goals = "N/A", "N/A", "N/A"
    except Exception:
        pending_tasks, active_meds, active_goals = "N/A", "N/A", "N/A"

    stat1 = create_stat_item(stats_frame, "Pending Tasks", pending_tasks, "#e74c3c")
    stat1.pack(side=LEFT, expand=True, fill=X, padx=5)
    stat2 = create_stat_item(stats_frame, "Active Meds", active_meds, "#16a085")
    stat2.pack(side=LEFT, expand=True, fill=X, padx=5)
    stat3 = create_stat_item(stats_frame, "Active Goals", active_goals, "#8e44ad")
    stat3.pack(side=LEFT, expand=True, fill=X, padx=5)

    # Welcome message with user name
    welcome_frame = Frame(content_frame, bg="#ecf0f1", relief="raised", bd=1)
    welcome_frame.pack(fill=X, padx=40, pady=10)
    
    welcome_text = f"✨ Welcome {current_user}! Manage your life efficiently ✨"
    Label(welcome_frame, text=welcome_text, 
          font=("Segoe UI", 16, "italic"), bg="#ecf0f1", fg="#34495e").pack(pady=15)

    # Cards container with better spacing
    cards_container = Frame(content_frame, bg="#f8f9fc")
    cards_container.pack(expand=True, fill=BOTH, padx=20, pady=20)

    def create_card(parent, emoji, title, command, color, hover_color):
        card_frame = Frame(parent, bg="#ffffff", relief="raised", bd=2)
        
        card = Button(card_frame, text=f"{emoji}\n{title}", width=18, height=8,
                      bg=color, fg="white", font=("Segoe UI", 14, "bold"),
                      relief="flat", bd=0, cursor="hand2", command=command,
                      wraplength=120, justify="center", activebackground=hover_color,
                      activeforeground="white")
        card.pack(padx=5, pady=5, fill=BOTH, expand=True)
        
        return card_frame

    # Card definitions with hover colors
    cards = [
        {"emoji": "✅", "title": "Tasks\nManagement", "command": lambda: tasks_show_ui(content_frame, connect_db, show_dashboard), "color": "#27ae60", "hover": "#229954"},
        {"emoji": "💰", "title": "Expense\nTracker", "command": lambda: expenses_show_ui(content_frame, connect_db, show_dashboard), "color": "#f39c12", "hover": "#e67e22"},
        {"emoji": "🎯", "title": "Goal\nSetting", "command": lambda: goals_show_ui(content_frame, connect_db, show_dashboard), "color": "#8e44ad", "hover": "#7d3c98"},
        {"emoji": "💊", "title": "Medication\nReminder", "command": lambda: medications_show_ui(content_frame, connect_db, show_dashboard), "color": "#16a085", "hover": "#138d75"},
        {"emoji": "🔧", "title": "Settings\n& Config", "command": show_settings, "color": "#34495e", "hover": "#2c3e50"},
    ]

    # Create grid layout for cards
    for i, card_info in enumerate(cards):
        row = i // 3
        col = i % 3
        
        card = create_card(cards_container, card_info["emoji"], card_info["title"], 
                          card_info["command"], card_info["color"], card_info["hover"])
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

    # Configure grid weights for responsive design
    for i in range(3):
        cards_container.columnconfigure(i, weight=1)
    for i in range(2):
        cards_container.rowconfigure(i, weight=1)

    # Footer with info
    footer_frame = Frame(content_frame, bg="#34495e", height=40)
    footer_frame.pack(fill=X, side=BOTTOM)
    footer_frame.pack_propagate(False)
    
    Label(footer_frame, text="💡 Manage your life efficiently with our integrated system | Direct Access Mode", 
          font=("Segoe UI", 11), bg="#34495e", fg="#ecf0f1").pack(pady=10)

    # removed inline show_tasks; delegated to tasks_ui.show_tasks

# === Other Sections ===
def show_expenses():
    """Wrapper to render the expenses UI in the content frame."""
    expenses_show_ui(content_frame, connect_db, show_dashboard)

def show_goals():
    """Wrapper to render the goals UI in the content frame."""
    goals_show_ui(content_frame, connect_db, show_dashboard)

def show_medications():
    """Wrapper to render the medications UI in the content frame."""
    medications_show_ui(content_frame, connect_db, show_dashboard)

def show_settings():
    clear_frame()
    
    header_frame = Frame(content_frame, bg="#34495e", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)
    
    Label(header_frame, text="🔧 Settings & Configuration", font=("Segoe UI", 24, "bold"),
          bg="#34495e", fg="#ffffff").pack(pady=15)
    
    Button(content_frame, text="🏠 Back to Dashboard", command=show_dashboard, 
           bg="#34495e", fg="white", font=("Segoe UI", 10), relief="flat").pack(pady=10)
    
    # Settings Panel
    settings_container = Frame(content_frame, bg="#ffffff", relief="raised", bd=2)
    settings_container.pack(fill=X, padx=40, pady=20)
    
    Label(settings_container, text="⚙️ Application Settings", font=("Segoe UI", 16, "bold"),
          bg="#ffffff", fg="#2c3e50").pack(pady=15)
    
    settings_frame = Frame(settings_container, bg="#ffffff")
    settings_frame.pack(pady=10, padx=20)
    
    Label(settings_frame, text=f"👤 Current User: {current_user}", 
          font=("Segoe UI", 12), bg="#ffffff", fg="#2c3e50").pack(pady=10, anchor=W)
    
    Label(settings_frame, text="🌟 Direct Access Mode Enabled", 
          font=("Segoe UI", 12), bg="#ffffff", fg="#27ae60").pack(pady=5, anchor=W)
    
    Button(settings_frame, text="🔄 Restart Application", 
           command=lambda: restart_app(),
           bg="#3498db", fg="white", font=("Segoe UI", 11, "bold"), 
           relief="flat", padx=20, pady=8).pack(pady=15)

def restart_app():
    result = messagebox.askyesno("Restart", "🔄 Are you sure you want to restart the application?")
    if result:
        try:
            if root is not None:
                root.destroy()
        finally:
            main()

# === Main GUI ===
def main():
    global root, content_frame, current_user

    # Resolve user name from CLI if provided
    user_id = parse_cli_user_id()
    if user_id:
        name = resolve_user_name(user_id)
        if name:
            current_user = name
        else:
            current_user = f"User {user_id}"

    root = Tk()
    root.title("🧠 Life Manager - Dashboard")
    root.geometry("1000x700")
    root.configure(bg="#ffffff")
    root.resizable(True, True)

    # Initialize widget styles once
    init_styles()

    # === Main content frame ===
    content_frame = Frame(root, bg="#f8f9fc")
    content_frame.pack(fill=BOTH, expand=True)

    # Show dashboard
    show_dashboard()

    # Center window after layout measurements
    center_window(root)

    root.minsize(900, 600)
    root.mainloop()

# Run the application
if __name__ == "__main__":
    main()
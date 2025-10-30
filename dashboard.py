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
from app_config import get_theme_colors, set_theme, set_language
from localization import get_text, TRANSLATIONS


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
    colors = get_theme_colors()
    content_frame.config(bg=colors["bg"])

    # Header with gradient-like effect
    header_frame = Frame(content_frame, bg=colors["header_bg"], height=80)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)

    Label(header_frame, text=get_text("dashboard_title"), font=("Segoe UI", 28, "bold"),
          bg=colors["header_bg"], fg=colors["header_fg"]).pack(side=LEFT, padx=20)

    # Clock and Date
    clock_frame = Frame(header_frame, bg=colors["header_bg"])
    clock_frame.pack(side=RIGHT, padx=20, pady=10)

    time_label = Label(clock_frame, font=("Segoe UI", 22, "bold"), bg=colors["header_bg"], fg=colors["header_fg"])
    time_label.pack()
    date_label = Label(clock_frame, font=("Segoe UI", 12), bg=colors["header_bg"], fg=colors["header_fg"])
    date_label.pack()

    def update_clock():
        now = datetime.now()
        time_label.config(text=now.strftime("%H:%M:%S"))
        date_label.config(text=now.strftime("%A, %B %d, %Y"))
        header_frame.after(1000, update_clock)

    update_clock()

    # Quick Stats
    stats_frame = Frame(content_frame, bg=colors["bg"])
    stats_frame.pack(fill=X, padx=40, pady=(0, 10))

    def create_stat_item(parent, label_key, value, color):
        frame = Frame(parent, bg=color, relief="raised", bd=1)
        Label(frame, text=get_text(label_key), font=("Segoe UI", 11, "bold"), bg=color, fg="white").pack(padx=10, pady=(5,0))
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
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE())")
            monthly_expense_raw = cursor.fetchone()[0]
            monthly_expense = f"${monthly_expense_raw:.2f}" if monthly_expense_raw else "$0.00"
            conn.close()
        else:
            pending_tasks, active_meds, active_goals, monthly_expense = "N/A", "N/A", "N/A", "N/A"
    except Exception:
        pending_tasks, active_meds, active_goals, monthly_expense = "N/A", "N/A", "N/A", "N/A"

    stat1 = create_stat_item(stats_frame, "pending_tasks", pending_tasks, "#e74c3c")
    stat1.pack(side=LEFT, expand=True, fill=X, padx=5)
    stat2 = create_stat_item(stats_frame, "active_meds", active_meds, "#16a085")
    stat2.pack(side=LEFT, expand=True, fill=X, padx=5)
    stat3 = create_stat_item(stats_frame, "active_goals", active_goals, "#8e44ad")
    stat3.pack(side=LEFT, expand=True, fill=X, padx=5)
    stat4 = create_stat_item(stats_frame, "monthly_expense", monthly_expense, "#f39c12")
    stat4.pack(side=LEFT, expand=True, fill=X, padx=5)

    # Welcome message with user name
    welcome_frame = Frame(content_frame, bg=colors["card_bg"], relief="raised", bd=1)
    welcome_frame.pack(fill=X, padx=40, pady=10)
    
    welcome_text = get_text("welcome_message", user=current_user)
    Label(welcome_frame, text=welcome_text, 
          font=("Segoe UI", 16, "italic"), bg=colors["card_bg"], fg=colors["fg"]).pack(pady=15)

    # Cards container with better spacing
    cards_container = Frame(content_frame, bg=colors["bg"])
    cards_container.pack(expand=True, fill=BOTH, padx=20, pady=20)

    def create_card(parent, emoji, title_key, command, color, hover_color):
        card_frame = Frame(parent, bg=colors["card_bg"], relief="solid", bd=1, highlightbackground="#e0e0e0", highlightthickness=1)
        card_frame.config(cursor="hand2")

        emoji_label = Label(card_frame, text=emoji, font=("Segoe UI", 32), bg=colors["card_bg"], fg=color)
        emoji_label.pack(pady=(20, 10))

        title_label = Label(card_frame, text=get_text(title_key), font=("Segoe UI", 13, "bold"), bg=colors["card_bg"], fg=colors["fg"], wraplength=150, justify="center")
        title_label.pack(pady=(0, 20), padx=10, fill="x")

        # --- Hover and Click Bindings ---
        def on_enter(e):
            card_frame.config(bg=hover_color)
            for child in card_frame.winfo_children():
                child.config(bg=hover_color, fg="white")

        def on_leave(e):
            card_frame.config(bg=colors["card_bg"])
            emoji_label.config(fg=color)
            title_label.config(fg=colors["fg"])

        # Bind events to all widgets for a seamless experience
        for widget in [card_frame, emoji_label, title_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda e: command())

        return card_frame

    # Card definitions with hover colors
    cards = [
        {"emoji": "✅", "title_key": "task_management", "command": lambda: tasks_show_ui(content_frame, connect_db, show_dashboard), "color": "#27ae60", "hover": "#2ecc71"},
        {"emoji": "💰", "title_key": "expense_tracker", "command": lambda: expenses_show_ui(content_frame, connect_db, show_dashboard), "color": "#f39c12", "hover": "#f1c40f"},
        {"emoji": "🎯", "title_key": "goal_setting", "command": lambda: goals_show_ui(content_frame, connect_db, show_dashboard), "color": "#8e44ad", "hover": "#9b59b6"},
        {"emoji": "💊", "title_key": "medication_reminder", "command": lambda: medications_show_ui(content_frame, connect_db, show_dashboard), "color": "#16a085", "hover": "#1abc9c"},
        {"emoji": "🔧", "title_key": "settings_config", "command": show_settings, "color": "#34495e", "hover": "#5d6d7e"},
    ]

    # Create grid layout for cards
    for i, card_info in enumerate(cards):
        row = i // 3
        col = i % 3
        
        card = create_card(cards_container, card_info["emoji"], card_info["title_key"], 
                          card_info["command"], card_info["color"], card_info["hover"])
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

    # Configure grid weights for responsive design
    for i in range(3):
        cards_container.columnconfigure(i, weight=1)
    for i in range(2):
        cards_container.rowconfigure(i, weight=1)

    # Footer with info
    footer_frame = Frame(content_frame, bg=colors["footer_bg"], height=40)
    footer_frame.pack(fill=X, side=BOTTOM)
    footer_frame.pack_propagate(False)
    
    Label(footer_frame, text=f'{get_text("footer_text")} | Direct Access Mode', 
          font=("Segoe UI", 11), bg=colors["footer_bg"], fg=colors["footer_fg"]).pack(pady=10)


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
    colors = get_theme_colors()
    content_frame.config(bg=colors["bg"])
    
    header_frame = Frame(content_frame, bg=colors["header_bg"], height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)
    
    Label(header_frame, text=get_text("settings_title"), font=("Segoe UI", 24, "bold"),
          bg=colors["header_bg"], fg=colors["header_fg"]).pack(pady=15)
    
    Button(content_frame, text=get_text("back_to_dashboard"), command=show_dashboard, 
           bg=colors["button_bg"], fg=colors["button_fg"], font=("Segoe UI", 10), relief="flat").pack(pady=10)
    
    # Settings Panel
    settings_container = Frame(content_frame, bg=colors["card_bg"], relief="raised", bd=2)
    settings_container.pack(fill=X, padx=40, pady=20)
    
    Label(settings_container, text=get_text("app_settings"), font=("Segoe UI", 16, "bold"),
          bg=colors["card_bg"], fg=colors["fg"]).pack(pady=15)
    
    settings_frame = Frame(settings_container, bg=colors["card_bg"])
    settings_frame.pack(pady=10, padx=20, fill=X)
    
    # Theme Selection
    theme_frame = Frame(settings_frame, bg=colors["card_bg"])
    theme_frame.pack(fill=X, pady=10)
    Label(theme_frame, text=get_text("theme_selection"), font=("Segoe UI", 12, "bold"), bg=colors["card_bg"], fg=colors["fg"]).pack(anchor=W)
    
    theme_var = StringVar(value="light")
    Radiobutton(theme_frame, text=get_text("light_theme"), variable=theme_var, value="light", bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(anchor=W)
    Radiobutton(theme_frame, text=get_text("dark_theme"), variable=theme_var, value="dark", bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(anchor=W)

    # Language Selection
    lang_frame = Frame(settings_frame, bg=colors["card_bg"])
    lang_frame.pack(fill=X, pady=10)
    Label(lang_frame, text=get_text("language_selection"), font=("Segoe UI", 12, "bold"), bg=colors["card_bg"], fg=colors["fg"]).pack(anchor=W)

    lang_var = StringVar(value="en")
    Radiobutton(lang_frame, text=get_text("english"), variable=lang_var, value="en", bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(anchor=W)
    Radiobutton(lang_frame, text=get_text("bengali"), variable=lang_var, value="bn", bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["bg"]).pack(anchor=W)

    def save_and_restart():
        set_theme(theme_var.get())
        set_language(lang_var.get())
        if messagebox.askyesno(get_text("restart_prompt_title"), get_text("restart_prompt_message")):
            restart_app()

    Button(settings_frame, text=get_text("save_settings"), 
           command=save_and_restart,
           bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"), 
           relief="flat", padx=20, pady=8).pack(pady=15)


def apply_theme(theme_name):
    """Apply selected theme to the application."""
    global current_theme
    current_theme = theme_name
    
    # Re-render the current view to apply the theme
    # This is a simple way to apply themes without complex style management
    show_dashboard()
    show_settings() # Re-show settings to update its own colors

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
    root.title(get_text("dashboard_title"))
    root.geometry("1000x700")
    root.configure(bg=get_theme_colors()["bg"])
    root.resizable(True, True)

    # Initialize widget styles once
    init_styles()

    # === Main content frame ===
    content_frame = Frame(root, bg=get_theme_colors()["bg"])
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
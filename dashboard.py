from tkinter import *
from tkinter import messagebox, ttk
import mysql.connector
import subprocess
import sys
import os

# === Database Connection ===
def connect_db():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="life_manger"
        )
        print("✅ Connected to MySQL database successfully!")
        return db
    except mysql.connector.Error as err:
        print("❌ Failed to connect:", err)
        return None

# === Global Variables (No login required) ===
current_user = "Admin"  # Default user

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
          bg="#2c3e50", fg="#ffffff").pack(pady=20)

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
        {"emoji": "✅", "title": "Tasks\nManagement", "command": show_tasks, "color": "#27ae60", "hover": "#229954"},
        {"emoji": "💰", "title": "Expense\nTracker", "command": show_expenses, "color": "#f39c12", "hover": "#e67e22"},
        {"emoji": "🎯", "title": "Goal\nSetting", "command": show_goals, "color": "#8e44ad", "hover": "#7d3c98"},
        {"emoji": "💊", "title": "Medication\nReminder", "command": show_medications, "color": "#16a085", "hover": "#138d75"},
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

# === Task CRUD Section ===
def show_tasks():
    clear_frame()

    # Enhanced header for tasks
    header_frame = Frame(content_frame, bg="#27ae60", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)

    Label(header_frame, text="✅ Task Management System", font=("Segoe UI", 24, "bold"),
          bg="#27ae60", fg="#ffffff").pack(pady=15)

    # Back button
    nav_frame = Frame(content_frame, bg="#f8f9fc")
    nav_frame.pack(fill=X, padx=20, pady=(0, 10))
    Button(nav_frame, text="🏠 Back to Dashboard", command=show_dashboard, 
           bg="#34495e", fg="white", font=("Segoe UI", 10), relief="flat").pack(side=LEFT)

    # Form container with better styling
    form_container = Frame(content_frame, bg="#ffffff", relief="raised", bd=2)
    form_container.pack(fill=X, padx=20, pady=10)

    Label(form_container, text="📝 Task Information", font=("Segoe UI", 16, "bold"),
          bg="#ffffff", fg="#2c3e50").pack(pady=10)

    form_frame = Frame(form_container, bg="#ffffff")
    form_frame.pack(pady=10, padx=20)

    # Enhanced form fields
    Label(form_frame, text="Task Title:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=0, column=0, sticky=W, pady=5)
    title_entry = Entry(form_frame, font=("Segoe UI", 12), width=25, relief="solid", bd=1)
    title_entry.grid(row=0, column=1, padx=10, pady=5, ipady=3)

    Label(form_frame, text="Description:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=1, column=0, sticky=W, pady=5)
    desc_entry = Entry(form_frame, font=("Segoe UI", 12), width=25, relief="solid", bd=1)
    desc_entry.grid(row=1, column=1, padx=10, pady=5, ipady=3)

    Label(form_frame, text="Priority Level:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=2, column=0, sticky=W, pady=5)
    priority_var = StringVar()
    priority_menu = OptionMenu(form_frame, priority_var, "Low", "Medium", "High")
    priority_menu.configure(font=("Segoe UI", 11), bg="#ecf0f1", relief="solid")
    priority_var.set("Medium")
    priority_menu.grid(row=2, column=1, padx=10, pady=5, sticky=W)

    Label(form_frame, text="Task Status:", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50").grid(row=3, column=0, sticky=W, pady=5)
    status_var = StringVar()
    status_menu = OptionMenu(form_frame, status_var, "Pending", "In Progress", "Completed")
    status_menu.configure(font=("Segoe UI", 11), bg="#ecf0f1", relief="solid")
    status_var.set("Pending")
    status_menu.grid(row=3, column=1, padx=10, pady=5, sticky=W)

    selected_task_id = StringVar()

    def clear_form():
        title_entry.delete(0, END)
        desc_entry.delete(0, END)
        priority_var.set("Medium")
        status_var.set("Pending")
        selected_task_id.set("")

    def refresh_table():
        for row in task_table.get_children():
            task_table.delete(row)

        db = connect_db()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT id, title, description, priority, status FROM tasks")
            for row in cursor.fetchall():
                task_table.insert("", END, values=row)
            db.close()

    def save_task():
        title = title_entry.get()
        desc = desc_entry.get()
        priority = priority_var.get()
        status = status_var.get()

        if not title:
            messagebox.showwarning("Validation Error", "⚠️ Task title is required.")
            return

        db = connect_db()
        if db:
            cursor = db.cursor()
            try:
                if selected_task_id.get():
                    cursor.execute("UPDATE tasks SET title=%s, description=%s, priority=%s, status=%s WHERE id=%s",
                                   (title, desc, priority, status, selected_task_id.get()))
                    messagebox.showinfo("Success", "✅ Task updated successfully!")
                else:
                    cursor.execute("INSERT INTO tasks (title, description, priority, status) VALUES (%s, %s, %s, %s)",
                                   (title, desc, priority, status))
                    messagebox.showinfo("Success", "✅ Task added successfully!")
                db.commit()
                clear_form()
                refresh_table()
            except Exception as e:
                messagebox.showerror("Database Error", f"❌ Error: {str(e)}")
            finally:
                db.close()

    def on_row_select(event):
        selected = task_table.focus()
        if selected:
            values = task_table.item(selected, "values")
            selected_task_id.set(values[0])
            title_entry.delete(0, END)
            title_entry.insert(0, values[1])
            desc_entry.delete(0, END)
            desc_entry.insert(0, values[2])
            priority_var.set(values[3])
            status_var.set(values[4])

    def delete_task():
        if not selected_task_id.get():
            messagebox.showwarning("Delete Task", "⚠️ Please select a task to delete.")
            return

        confirm = messagebox.askyesno("Delete Task", "🗑️ Are you sure you want to delete this task?")
        if confirm:
            db = connect_db()
            if db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM tasks WHERE id=%s", (selected_task_id.get(),))
                db.commit()
                db.close()
                clear_form()
                refresh_table()
                messagebox.showinfo("Deleted", "✅ Task deleted successfully!")

    # Enhanced buttons with better styling
    button_frame = Frame(form_container, bg="#ffffff")
    button_frame.pack(pady=15)
    
    Button(button_frame, text="💾 Save Task", command=save_task, 
           bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"), 
           relief="flat", padx=20, pady=8).grid(row=0, column=0, padx=8)
    Button(button_frame, text="♻️ Reset Form", command=clear_form, 
           bg="#3498db", fg="white", font=("Segoe UI", 11, "bold"), 
           relief="flat", padx=20, pady=8).grid(row=0, column=1, padx=8)
    Button(button_frame, text="🗑️ Delete Task", command=delete_task, 
           bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"), 
           relief="flat", padx=20, pady=8).grid(row=0, column=2, padx=8)

    # Enhanced table container
    table_container = Frame(content_frame, bg="#ffffff", relief="raised", bd=2)
    table_container.pack(fill=BOTH, expand=True, padx=20, pady=10)

    Label(table_container, text="📊 Your Tasks Overview", font=("Segoe UI", 16, "bold"),
          bg="#ffffff", fg="#2c3e50").pack(pady=10)

    # Task Table with enhanced styling
    style = ttk.Style()
    style.configure("Custom.Treeview.Heading", font=("Segoe UI", 11, "bold"))
    style.configure("Custom.Treeview", font=("Segoe UI", 10))

    task_table = ttk.Treeview(table_container, columns=("ID", "Title", "Description", "Priority", "Status"), 
                             show="headings", style="Custom.Treeview")
    
    # Configure columns
    task_table.heading("ID", text="🆔 ID")
    task_table.heading("Title", text="📝 Title")
    task_table.heading("Description", text="📋 Description")
    task_table.heading("Priority", text="⚡ Priority")
    task_table.heading("Status", text="📊 Status")
    
    task_table.column("ID", width=60, anchor=CENTER)
    task_table.column("Title", width=150, anchor=W)
    task_table.column("Description", width=200, anchor=W)
    task_table.column("Priority", width=100, anchor=CENTER)
    task_table.column("Status", width=120, anchor=CENTER)
    
    task_table.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
    task_table.bind("<ButtonRelease-1>", on_row_select)

    refresh_table()

# === Other Sections ===
def show_expenses():
    clear_frame()
    
    header_frame = Frame(content_frame, bg="#f39c12", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)
    
    Label(header_frame, text="💰 Expense Management System", font=("Segoe UI", 24, "bold"),
          bg="#f39c12", fg="#ffffff").pack(pady=15)
    
    Button(content_frame, text="🏠 Back to Dashboard", command=show_dashboard, 
           bg="#34495e", fg="white", font=("Segoe UI", 10), relief="flat").pack(pady=10)

    # Centering container
    center_frame = Frame(content_frame, bg="#f8f9fc")
    center_frame.pack(expand=True, fill=BOTH)
    Label(center_frame, text="📊 Expense Management will be implemented soon..", 
          font=("Segoe UI", 16), bg="#f8f9fc", fg="#7f8c8d").place(relx=0.5, rely=0.5, anchor=CENTER)

def show_goals():
    clear_frame()
    
    header_frame = Frame(content_frame, bg="#8e44ad", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)
    
    Label(header_frame, text="🎯 Goal Achievement System", font=("Segoe UI", 24, "bold"),
          bg="#8e44ad", fg="#ffffff").pack(pady=15)
    
    Button(content_frame, text="🏠 Back to Dashboard", command=show_dashboard, 
           bg="#34495e", fg="white", font=("Segoe UI", 10), relief="flat").pack(pady=10)
    
    center_frame = Frame(content_frame, bg="#f8f9fc")
    center_frame.pack(expand=True, fill=BOTH)
    Label(center_frame, text="🌟 Goal Setting Module - Coming Soon!",
          font=("Segoe UI", 16), bg="#f8f9fc", fg="#7f8c8d").place(relx=0.5, rely=0.5, anchor=CENTER)

def show_medications():
    clear_frame()
    
    header_frame = Frame(content_frame, bg="#16a085", height=70)
    header_frame.pack(fill=X, pady=(0, 20))
    header_frame.pack_propagate(False)
    
    Label(header_frame, text="💊 Medication Reminder System", font=("Segoe UI", 24, "bold"),
          bg="#16a085", fg="#ffffff").pack(pady=15)
    
    Button(content_frame, text="🏠 Back to Dashboard", command=show_dashboard, 
           bg="#34495e", fg="white", font=("Segoe UI", 10), relief="flat").pack(pady=10)
    
    center_frame = Frame(content_frame, bg="#f8f9fc")
    center_frame.pack(expand=True, fill=BOTH)
    Label(center_frame, text="⏰ Medication Tracking - Under Development", 
          font=("Segoe UI", 16), bg="#f8f9fc", fg="#7f8c8d").place(relx=0.5, rely=0.5, anchor=CENTER)

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
        root.destroy()
        main()

# === Main GUI ===
def main():
    global root, content_frame
    
    root = Tk()
    root.title("🧠 Life Manager - Direct Dashboard")
    root.geometry("1000x700")
    root.configure(bg="#ffffff")
    root.resizable(True, True)
    
    # Maximize window on Windows
    try:
        root.state('zoomed')
    except:
        pass

    # === Main content frame ===
    content_frame = Frame(root, bg="#f8f9fc")
    content_frame.pack(fill=BOTH, expand=True)

    # Start directly with dashboard (no login)
    show_dashboard()
    root.mainloop()

# Run the application
if __name__ == "__main__":
    main()
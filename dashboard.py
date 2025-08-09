from tkinter import *
from tkinter import messagebox
import mysql.connector

# === Database Connection ===
def connect_db():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="life_manager"
        )
        return db
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"❌ Failed to connect to database:\n{err}")
        return None

# === Dummy functions for button clicks ===
def show_dashboard():
    clear_frame()
    Label(content_frame, text="🏠 Welcome to Dashboard", font=("Segoe UI", 24, "bold"), 
          bg="#f8f9fc", fg="#2c3e50").pack(pady=40)

def show_tasks():
    clear_frame()
    Label(content_frame, text="✅ Tasks Section", font=("Segoe UI", 24, "bold"), 
          bg="#f8f9fc", fg="#2c3e50").pack(pady=20)

    Label(content_frame, text="Task Title:", font=("Segoe UI", 12), bg="#f8f9fc").pack()
    title_entry = Entry(content_frame, font=("Segoe UI", 12))
    title_entry.pack(pady=5)

    Label(content_frame, text="Description:", font=("Segoe UI", 12), bg="#f8f9fc").pack()
    desc_entry = Entry(content_frame, font=("Segoe UI", 12))
    desc_entry.pack(pady=5)

    def add_task():
        title = title_entry.get()
        desc = desc_entry.get()
        if not title:
            messagebox.showwarning("Validation", "Title is required")
            return
        db = connect_db()
        if db:
            cursor = db.cursor()
            cursor.execute("INSERT INTO tasks (title, description) VALUES (%s, %s)", (title, desc))
            db.commit()
            db.close()
            messagebox.showinfo("Success", "Task added successfully!")
            title_entry.delete(0, END)
            desc_entry.delete(0, END)

    Button(content_frame, text="+ Add Task", bg="#2ecc71", fg="white", font=("Segoe UI", 12, "bold"), 
           command=add_task).pack(pady=10)

def show_expenses():
    clear_frame()
    Label(content_frame, text="💰 Expenses Section", font=("Segoe UI", 24, "bold"), 
          bg="#f8f9fc", fg="#2c3e50").pack(pady=40)

def show_goals():
    clear_frame()
    Label(content_frame, text="🎯 Goals Section", font=("Segoe UI", 24, "bold"), 
          bg="#f8f9fc", fg="#2c3e50").pack(pady=40)
    Label(content_frame, text="Set your personal development goals here.", 
          font=("Segoe UI", 14), bg="#f8f9fc", fg="#7f8c8d").pack(pady=10)

def show_medications():
    clear_frame()
    Label(content_frame, text="💊 Medication Reminder", font=("Segoe UI", 24, "bold"), 
          bg="#f8f9fc", fg="#2c3e50").pack(pady=40)

def logout():
    root.destroy()
    import login  # Reload login window

# === Clear content before loading next ===
def clear_frame():
    for widget in content_frame.winfo_children():
        widget.destroy()

# === Button hover effects ===
def on_button_hover(button, hover_color):
    button.config(bg=hover_color)

def on_button_leave(button, normal_color):
    button.config(bg=normal_color)

def create_styled_button(parent, text, command, bg_color, hover_color="#2c3e50"):
    btn = Button(parent, text=text, bg=bg_color, fg="white", 
                font=("Segoe UI", 12, "bold"), width=18, height=2,
                relief="flat", bd=0, command=command, cursor="hand2",
                activebackground=hover_color, activeforeground="white")
    btn.pack(pady=8, padx=15, fill=X)
    btn.bind("<Enter>", lambda e: on_button_hover(btn, hover_color))
    btn.bind("<Leave>", lambda e: on_button_leave(btn, bg_color))
    return btn

# === Main GUI ===
root = Tk()
root.title("🧠 Life Manager - Dashboard")
root.geometry("900x600")
root.configure(bg="#ffffff")
root.resizable(True, True)

# === Sidebar ===
sidebar = Frame(root, bg="#2c3e50", width=250)
sidebar.pack(side=LEFT, fill=Y)
sidebar.pack_propagate(False)

header_frame = Frame(sidebar, bg="#34495e", height=100)
header_frame.pack(fill=X, pady=(0, 30))
header_frame.pack_propagate(False)

Label(header_frame, text="☁️ Life Manager", bg="#34495e", fg="white", 
      font=("Segoe UI", 18, "bold")).pack(expand=True, pady=20)

create_styled_button(sidebar, "🏠 Dashboard", show_dashboard, "#3498db", "#2980b9")
create_styled_button(sidebar, "✅ Tasks", show_tasks, "#2ecc71", "#27ae60")
create_styled_button(sidebar, "💰 Expenses", show_expenses, "#f39c12", "#e67e22")
create_styled_button(sidebar, "🎯 Goals", show_goals, "#9b59b6", "#8e44ad")
create_styled_button(sidebar, "💊 Medication", show_medications, "#1abc9c", "#16a085")

Frame(sidebar, bg="#2c3e50", height=60).pack()
create_styled_button(sidebar, "🔓 Logout", logout, "#e74c3c", "#c0392b")

footer_frame = Frame(sidebar, bg="#2c3e50")
footer_frame.pack(side=BOTTOM, fill=X, pady=20)

Label(footer_frame, text="v1.0", bg="#2c3e50", fg="#7f8c8d", 
      font=("Segoe UI", 10)).pack()

# === Main content frame ===
content_frame = Frame(root, bg="#f8f9fc")
content_frame.pack(side=RIGHT, fill=BOTH, expand=True)

border_frame = Frame(root, bg="#bdc3c7", width=1)
border_frame.pack(side=LEFT, fill=Y)

show_dashboard()
root.mainloop()

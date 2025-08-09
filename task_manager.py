from tkinter import *
from tkinter import messagebox
import mysql.connector
from datetime import datetime

# ======== Database Connection =========
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

if __name__ == "__main__":
    connection = connect_db()
    if connection:
        connection.close()

# ======== Insert Task into Database =========
def add_task():
    title = title_entry.get()
    priority = priority_var.get()
    due_date = due_date_entry.get()
    status = status_var.get()

    if title == "" or due_date == "":
        messagebox.showwarning("Warning", "Title and Due Date are required!")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title, priority, due_date, status) VALUES (%s, %s, %s, %s)",
                       (title, priority, due_date, status))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "✅ Task added successfully!")
        clear_fields()
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong:\n{e}")

# ======== Clear Form Fields =========
def clear_fields():
    title_entry.delete(0, END)
    due_date_entry.delete(0, END)
    priority_var.set("Medium")
    status_var.set("Pending")

# ======== Main Window =========
root = Tk()
root.title("Add Task - Life Manager")
root.geometry("400x350")
root.config(bg="#ecf0f1")

Label(root, text="➕ Add New Task", font=("Helvetica", 16, "bold"), bg="#ecf0f1").pack(pady=10)

# ======== Form Frame =========
form_frame = Frame(root, bg="#ecf0f1")
form_frame.pack(pady=10)

# --- Title
Label(form_frame, text="Task Title:", bg="#ecf0f1").grid(row=0, column=0, sticky="w")
title_entry = Entry(form_frame, width=30)
title_entry.grid(row=0, column=1, pady=5)

# --- Priority
Label(form_frame, text="Priority:", bg="#ecf0f1").grid(row=1, column=0, sticky="w")
priority_var = StringVar(value="Medium")
priority_menu = OptionMenu(form_frame, priority_var, "High", "Medium", "Low")
priority_menu.grid(row=1, column=1, pady=5)

# --- Due Date
Label(form_frame, text="Due Date (YYYY-MM-DD):", bg="#ecf0f1").grid(row=2, column=0, sticky="w")
due_date_entry = Entry(form_frame, width=30)
due_date_entry.grid(row=2, column=1, pady=5)

# --- Status
Label(form_frame, text="Status:", bg="#ecf0f1").grid(row=3, column=0, sticky="w")
status_var = StringVar(value="Pending")
status_menu = OptionMenu(form_frame, status_var, "Pending", "In Progress", "Completed")
status_menu.grid(row=3, column=1, pady=5)

# ======== Buttons =========
Button(root, text="✅ Add Task", bg="#27ae60", fg="white", width=15, command=add_task).pack(pady=10)
Button(root, text="❌ Clear", bg="#c0392b", fg="white", width=15, command=clear_fields).pack()

root.mainloop()

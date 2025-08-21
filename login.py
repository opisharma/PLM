from tkinter import *
from tkinter import messagebox
import mysql.connector
import subprocess
import hashlib


# === Database connection ===
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# === Login function ===
def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showwarning("Validation", "⚠️ All fields are required!")
        return

    try:
        db = connect_db()
        if db is None:
            return

        cursor = db.cursor()
        hashed_pw = hash_password(password)
        query = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, hashed_pw))
        result = cursor.fetchone()
        db.close()

        if result:
            messagebox.showinfo("Login Success", "🎉 Welcome to Life Manager!")
            root.destroy()
            subprocess.Popen(["python", "dashboard.py"])  # ✅ Show dashboard
        else:
            messagebox.showerror("Login Failed", "❌ Invalid username or password!")

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))

# === UI ===
root = Tk()
root.title("Login - Life Manager")
root.geometry("400x300")
root.configure(bg="#ecf0f1")

Label(root, text="Login to Life Manager", font=("Segoe UI", 16, "bold"), bg="#ecf0f1").pack(pady=20)

Label(root, text="Username", bg="#ecf0f1").pack()
username_entry = Entry(root, font=("Segoe UI", 12))
username_entry.pack(pady=5)

Label(root, text="Password", bg="#ecf0f1").pack()
password_entry = Entry(root, show="*", font=("Segoe UI", 12))
password_entry.pack(pady=5)

Button(root, text="Login", command=login,
       bg="#3498db", fg="white", font=("Segoe UI", 12, "bold"), width=20).pack(pady=20)

root.mainloop()
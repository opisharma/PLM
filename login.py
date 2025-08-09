from tkinter import *
from tkinter import messagebox
import mysql.connector
import hashlib

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

if __name__ == "__main__":
    connection = connect_db()
    if connection:
        connection.close()

# === Password Hashing (same as registration) ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# === Dummy Task Page after login ===
def task_page(username):
    login_window.destroy()
    task_win = Tk()
    task_win.title("🧠 Life Manager - Dashboard")
    task_win.geometry("400x300")
    Label(task_win, text=f"Welcome, {username}!", font=("Arial", 16)).pack(pady=20)
    Label(task_win, text="🎯 This is your Task Page.").pack()
    task_win.mainloop()

# === Login Logic ===
def login_user():
    username = username_entry.get()
    password = password_entry.get()

    if username == "" or password == "":
        messagebox.showwarning("Warning", "সব ফিল্ড পূরণ করুন")
        return

    hashed_pw = hash_password(password)

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, hashed_pw))
        user = cursor.fetchone()
        conn.close()

        if user:
            messagebox.showinfo("Success", "✅ Login Successful")
            login_window.destroy()
            import dashboard  # ⬅⬅⬅ এই লাইন নিশ্চিত করো
        else:
            messagebox.showerror("Error", "❌ ভুল Username বা Password")

    except Exception as e:
        messagebox.showerror("Error", f"ডেটাবেজে সমস্যা:\n{e}")


# === GUI Layout ===
login_window = Tk()
login_window.title("Life Manager - Login")
login_window.geometry("350x250")
login_window.config(bg="#ecf0f1")

Label(login_window, text="🔐 User Login", font=("Helvetica", 16), bg="#ecf0f1").pack(pady=10)

form = Frame(login_window, bg="#ecf0f1")
form.pack(pady=10)

Label(form, text="Username:", bg="#ecf0f1").grid(row=0, column=0, sticky="w")
username_entry = Entry(form, width=30)
username_entry.grid(row=0, column=1, pady=5)

Label(form, text="Password:", bg="#ecf0f1").grid(row=1, column=0, sticky="w")
password_entry = Entry(form, show="*", width=30)
password_entry.grid(row=1, column=1, pady=5)

Button(login_window, text="🔓 Login", bg="#2980b9", fg="white", width=20, command=login_user).pack(pady=15)

login_window.mainloop()

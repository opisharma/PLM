from tkinter import *
from tkinter import messagebox
import mysql.connector
import hashlib

# === Database Connection ===
import mysql.connector

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


# === Hash Password ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# === Registration Logic ===
def register_user():
    username = username_entry.get()
    email = email_entry.get()
    password = password_entry.get()

    if username == "" or email == "" or password == "":
        messagebox.showwarning("Warning", "fullfield all please")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()

        hashed_pw = hash_password(password)

        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, hashed_pw))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "✅ Registration Sucessfull!")
        root.destroy() 

    except mysql.connector.IntegrityError:
        messagebox.showerror("Error", "❌ Username or Email already exist")
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong:\n{e}")

# === GUI Layout ===
root = Tk()
root.title("Life Manager - Register")
root.geometry("350x300")
root.config(bg="#ecf0f1")

Label(root, text="🔐 User Registration", font=("Helvetica", 16), bg="#ecf0f1").pack(pady=10)

form = Frame(root, bg="#ecf0f1")
form.pack(pady=10)

Label(form, text="Username:", bg="#ecf0f1").grid(row=0, column=0, sticky="w")
username_entry = Entry(form, width=30)
username_entry.grid(row=0, column=1, pady=5)

Label(form, text="Email:", bg="#ecf0f1").grid(row=1, column=0, sticky="w")
email_entry = Entry(form, width=30)
email_entry.grid(row=1, column=1, pady=5)

Label(form, text="Password:", bg="#ecf0f1").grid(row=2, column=0, sticky="w")
password_entry = Entry(form, show="*", width=30)
password_entry.grid(row=2, column=1, pady=5)

Button(root, text="✅ Register", bg="#27ae60", fg="white", width=20, command=register_user).pack(pady=15)

root.mainloop()

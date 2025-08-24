import os
import re
import hashlib
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import mysql.connector
from db_connect import connect_db


DB_CONFIG = {
    "host": os.getenv("LM_DB_HOST", "localhost"),
    "user": os.getenv("LM_DB_USER", "root"),
    "password": os.getenv("LM_DB_PASSWORD", "1234"),
    "database": os.getenv("LM_DB_NAME", "life_manger"),  # set LM_DB_NAME=life_manager if needed
}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_valid_email(email: str) -> bool:
    # Simple RFC-5322-inspired check
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email) is not None


class RegisterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Life Manager - Register")
        self.root.geometry("360x320")
        self.root.config(bg="#ecf0f1")

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.dob_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self):
        tk.Label(self.root, text="🔐 User Registration", font=("Helvetica", 16), bg="#ecf0f1").pack(pady=10)

        form = tk.Frame(self.root, bg="#ecf0f1")
        form.pack(pady=10, padx=10, fill="x")

        # Name
        tk.Label(form, text="Name:", bg="#ecf0f1").grid(row=0, column=0, sticky="w")
        tk.Entry(form, width=30, textvariable=self.name_var).grid(row=0, column=1, pady=5)

        # Email
        tk.Label(form, text="Email:", bg="#ecf0f1").grid(row=1, column=0, sticky="w")
        tk.Entry(form, width=30, textvariable=self.email_var).grid(row=1, column=1, pady=5)

        # DOB
        tk.Label(form, text="Date of Birth (YYYY-MM-DD):", bg="#ecf0f1").grid(row=2, column=0, sticky="w")
        tk.Entry(form, width=30, textvariable=self.dob_var).grid(row=2, column=1, pady=5)

        # Phone
        tk.Label(form, text="Phone:", bg="#ecf0f1").grid(row=3, column=0, sticky="w")
        tk.Entry(form, width=30, textvariable=self.phone_var).grid(row=3, column=1, pady=5)

        # Password
        tk.Label(form, text="Password:", bg="#ecf0f1").grid(row=4, column=0, sticky="w")
        tk.Entry(form, show="*", width=30, textvariable=self.password_var).grid(row=4, column=1, pady=5)

        tk.Button(self.root, text="✅ Register", bg="#27ae60", fg="white", width=20, command=self.register_user).pack(pady=15)

    def register_user(self):
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        date_of_birth = self.dob_var.get().strip()
        phone = self.phone_var.get().strip()
        password = self.password_var.get()

        # Basic validation
        if not all([name, email, date_of_birth, phone, password]):
            messagebox.showwarning("Warning", "Please fill in all fields.")
            return

        if not is_valid_email(email):
            messagebox.showwarning("Warning", "Please enter a valid email address.")
            return

        # Date validation (YYYY-MM-DD)
        try:
            datetime.strptime(date_of_birth, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Warning", "Date of Birth must be in YYYY-MM-DD format.")
            return

        # Phone validation (digits, 7-15 length)
        if not phone.isdigit() or not (7 <= len(phone) <= 15):
            messagebox.showwarning("Warning", "Phone must be digits only (7-15 characters).")
            return

        conn = connect_db()
        if not conn:
            messagebox.showerror("Error", "Database connection failed.")
            return

        try:
            cursor = conn.cursor()
            try:
                hashed_pw = hash_password(password)
                cursor.execute(
                    """
                    INSERT INTO users (name, email, password, date_of_birth, phone)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (name, email, hashed_pw, date_of_birth, phone),
                )
                conn.commit()
            finally:
                cursor.close()

            messagebox.showinfo("Success", "✅ Registration Successful!")
            self.root.destroy()

        except mysql.connector.IntegrityError as e:
            # Rely on DB unique constraints for email/phone
            messagebox.showerror("Error", "❌ Email or Phone already exists.")
        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong:\n{e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    # Quick connectivity check (optional)
    # conn = connect_db()
    # if conn: conn.close()

    root = tk.Tk()
    app = RegisterApp(root)
    root.mainloop()

import re
import hashlib
import os
import sys
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import mysql.connector
from db_connect import connect_db
try:
    from tkcalendar import DateEntry  # type: ignore
except Exception:
    DateEntry = None  # Fallback if tkcalendar isn't installed


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_valid_email(email: str) -> bool:
    # Simple RFC-5322-inspired check
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email) is not None


class RegisterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Life Manager - Register")
        self.root.geometry("640x520")
        self.root.resizable(True, True)
        self.root.configure(bg="#ecf0f1")

        # Form variables
        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.dob_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.password_var = tk.StringVar()

        # Initialize DOB with today's date to ensure a valid default
        try:
            self.dob_var.set(datetime.today().strftime("%Y-%m-%d"))
        except Exception:
            pass

        self._build_ui()
        self._center_window()

    def _build_ui(self):
        # Header bar like login page
            # Header bar like login page
            header_frame = tk.Frame(self.root, bg="#3498db", height=60)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)

            tk.Label(
                header_frame,
                text="🔐 Life Manager Register",
                font=("Segoe UI", 18, "bold"),
                bg="#3498db",
                fg="white",
            ).pack(expand=True)

            # Main content like login page
            main_frame = tk.Frame(self.root, bg="#ecf0f1")
            main_frame.pack(expand=True, fill="both", padx=40, pady=30)

            label_font = ("Segoe UI", 12)
            entry_opts = {"font": ("Segoe UI", 12), "relief": "solid", "borderwidth": 1, "bg": "white", "width": 30}

            # Grid form for aligned rows without stretching in fullscreen
            form = tk.Frame(main_frame, bg="#ecf0f1")
            form.pack(fill="x")
            form.grid_columnconfigure(0, weight=0)
            form.grid_columnconfigure(1, weight=0)

            # Name
            tk.Label(form, text="Name:", font=label_font, bg="#ecf0f1").grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
            tk.Entry(form, textvariable=self.name_var, **entry_opts).grid(row=0, column=1, sticky="w", pady=6, ipady=4)

            # Email
            tk.Label(form, text="Email:", font=label_font, bg="#ecf0f1").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
            tk.Entry(form, textvariable=self.email_var, **entry_opts).grid(row=1, column=1, sticky="w", pady=6, ipady=4)

            # Date of Birth
            tk.Label(form, text="Date of Birth (YYYY-MM-DD):", font=label_font, bg="#ecf0f1").grid(row=2, column=0, sticky="e", padx=(0, 10), pady=6)
            if DateEntry is not None:
                self.dob_input = DateEntry(
                    form,
                    textvariable=self.dob_var,
                    date_pattern="yyyy-mm-dd",
                    showweeknumbers=False,
                    state="readonly",
                    width=28,
                )
                self.dob_input.grid(row=2, column=1, sticky="w", pady=6)
            else:
                tk.Entry(form, textvariable=self.dob_var, **entry_opts).grid(row=2, column=1, sticky="w", pady=6, ipady=4)

            # Phone
            tk.Label(form, text="Phone:", font=label_font, bg="#ecf0f1").grid(row=3, column=0, sticky="e", padx=(0, 10), pady=6)
            tk.Entry(form, textvariable=self.phone_var, **entry_opts).grid(row=3, column=1, sticky="w", pady=6, ipady=4)

            # Password
            tk.Label(form, text="Password:", font=label_font, bg="#ecf0f1").grid(row=4, column=0, sticky="e", padx=(0, 10), pady=6)
            tk.Entry(form, show="*", textvariable=self.password_var, **entry_opts).grid(row=4, column=1, sticky="w", pady=(6, 12), ipady=4)

            # Register button styled like login button
            tk.Button(
                main_frame,
                text="Register",
                command=self.register_user,
                bg="#3498db",
                fg="white",
                font=("Segoe UI", 12, "bold"),
                width=25,
                height=2,
                relief="flat",
                activebackground="#2980b9",
                activeforeground="white",
                cursor="hand2",
            ).pack(pady=10)

            # Login link below the button
            link_frame = tk.Frame(main_frame, bg="#ecf0f1")
            link_frame.pack(pady=6)

            link_text = tk.Label(link_frame, text="Already have an account? ", font=("Segoe UI", 10), bg="#ecf0f1", fg="#7f8c8d")
            link_text.pack(side="left")

            login_link = tk.Label(link_frame, text="Log in here", font=("Segoe UI", 10, "underline"), bg="#ecf0f1", fg="#3498db", cursor="hand2")
            login_link.pack(side="left")
            login_link.bind("<Button-1>", lambda e: self._go_to_login())

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
            self._go_to_login()

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

    def _center_window(self):
        # Center the window after widgets are laid out
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        # Keep a reasonable minimum size but allow shrinking for mini window
        self.root.minsize(360, 420)

    def _go_to_login(self):
        """Open the login window and close the register window."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            login_path = os.path.join(script_dir, "login.py")
            if os.path.exists(login_path):
                subprocess.Popen([sys.executable, login_path], cwd=script_dir)
                try:
                    self.root.quit()
                except Exception:
                    pass
                try:
                    self.root.destroy()
                except Exception:
                    pass
            else:
                messagebox.showerror("Error", "login.py file not found!")
        except Exception as e:
            messagebox.showerror("Navigation Error", f"Failed to open login page: {e}")


if __name__ == "__main__":
    # Quick connectivity check (optional)
    # conn = connect_db()
    # if conn: conn.close()

    root = tk.Tk()
    app = RegisterApp(root)
    root.mainloop()

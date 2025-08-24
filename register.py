import re
import hashlib
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
        # Outer content container to manage centering and responsiveness
        content = tk.Frame(self.root, bg="#ecf0f1")
        content.pack(expand=True, fill="both")

        # Grid weights to center child frame both horizontally and vertically
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(2, weight=1)

        # Center card
        card = tk.Frame(content, bg="#ecf0f1")
        card.grid(row=1, column=1, padx=20, pady=20)

        header = tk.Label(card, text="🔐 User Registration", font=("Helvetica", 18, "bold"), bg="#ecf0f1", fg="#2c3e50")
        header.pack(pady=(0, 10))

        form = tk.Frame(card, bg="#ecf0f1")
        form.pack(fill="x")
        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=0)

        label_opts = {"bg": "#ecf0f1", "fg": "#2c3e50", "font": ("Segoe UI", 11)}
        entry_opts = {"font": ("Segoe UI", 11)}

        # Name
        tk.Label(form, text="Name:", **label_opts).grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
        tk.Entry(form, textvariable=self.name_var, **entry_opts).grid(row=0, column=1, sticky="ew", pady=6, ipady=3)

        # Email
        tk.Label(form, text="Email:", **label_opts).grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
        tk.Entry(form, textvariable=self.email_var, **entry_opts).grid(row=1, column=1, sticky="ew", pady=6, ipady=3)

        # DOB with calendar picker
        tk.Label(form, text="Date of Birth (YYYY-MM-DD):", **label_opts).grid(row=2, column=0, sticky="e", padx=(0, 10), pady=6)
        if DateEntry is not None:
            def _open_calendar():
                try:
                    if hasattr(self.dob_input, "drop_down"):
                        self.dob_input.drop_down()
                    else:
                        self.dob_input.event_generate("<Button-1>")
                except Exception:
                    try:
                        self.dob_input.event_generate("<Button-1>")
                    except Exception:
                        pass

            self.dob_input = DateEntry(
                form,
                textvariable=self.dob_var,
                date_pattern="yyyy-mm-dd",
                showweeknumbers=False,
                state="readonly",
            )
            self.dob_input.grid(row=2, column=1, sticky="ew", pady=6, ipady=1)
            tk.Button(form, text="📅", width=3, command=_open_calendar).grid(row=2, column=2, padx=(6, 0))
        else:
            # Fallback: plain entry + hint to install tkcalendar for picker
            tk.Entry(form, textvariable=self.dob_var, **entry_opts).grid(row=2, column=1, sticky="ew", pady=6, ipady=3)
            def _explain_calendar():
                messagebox.showinfo(
                    "Enable Date Picker",
                    "To pick a date using a calendar, install the 'tkcalendar' package.\n\n"
                    "Example: pip install tkcalendar"
                )
            # tk.Button(form, text="📅", width=3, command=_explain_calendar).grid(row=2, column=2, padx=(6, 0))

        # Phone
        tk.Label(form, text="Phone:", **label_opts).grid(row=3, column=0, sticky="e", padx=(0, 10), pady=6)
        tk.Entry(form, textvariable=self.phone_var, **entry_opts).grid(row=3, column=1, sticky="ew", pady=6, ipady=3)

        # Password
        tk.Label(form, text="Password:", **label_opts).grid(row=4, column=0, sticky="e", padx=(0, 10), pady=6)
        tk.Entry(form, show="*", textvariable=self.password_var, **entry_opts).grid(row=4, column=1, sticky="ew", pady=6, ipady=3)

        # Submit button centered
        tk.Button(card, text="✅ Register", bg="#27ae60", fg="white", width=20, command=self.register_user, activebackground="#229954", relief="flat").pack(pady=15)

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


if __name__ == "__main__":
    # Quick connectivity check (optional)
    # conn = connect_db()
    # if conn: conn.close()

    root = tk.Tk()
    app = RegisterApp(root)
    root.mainloop()

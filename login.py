import tkinter as tk
from tkinter import messagebox
import subprocess
import hashlib
import os
import sys
from db_connect import connect_db

# === Database connection ===
# Use shared connection helper from db_connect.py to keep a single source of truth

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# === Module-level GUI references (initialized when UI is created) ===
root = None
email_entry = None
password_entry = None
login_btn = None

# === Dashboard launching function ===
def launch_dashboard(user_data=None):
    """Launch dashboard in a separate process with optional user data."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_path = os.path.join(script_dir, "dashboard.py")

        if not os.path.exists(dashboard_path):
            messagebox.showerror("Dashboard Error", "Dashboard file 'dashboard.py' not found.")
            return False

        args = [sys.executable, dashboard_path]
        if user_data and 'id' in user_data:
            args.append(f"--user_id={user_data.get('id', '')}")

        # Hide login window immediately while launching dashboard to avoid overlap
        try:
            if root is not None and root.winfo_exists():
                root.withdraw()
        except Exception:
            pass

        subprocess.Popen(args, cwd=script_dir)
        return True

    except Exception as e:
        # If launch failed, restore the login window
        try:
            if root is not None and root.winfo_exists():
                root.deiconify()
        except Exception:
            pass
        messagebox.showerror("Dashboard Error", f"Failed to launch dashboard: {str(e)}")
        return False

def open_register():
    """Open the registration window and close the login window."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        register_path = os.path.join(script_dir, "register.py")
        if os.path.exists(register_path):
            subprocess.Popen([sys.executable, register_path], cwd=script_dir)
            # Safely close current window if it exists
            try:
                if root is not None and root.winfo_exists():
                    root.quit()
                    root.destroy()
            except Exception:
                pass
        else:
            messagebox.showerror("Navigation Error", "Registration file 'register.py' not found.")
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Failed to open register page: {str(e)}")

# === Login function ===
def login():
    email = email_entry.get().strip()
    password = password_entry.get().strip()

    # Input validation
    if not email or not password:
        messagebox.showwarning("Validation Error", "Please enter both email and password.")
        return

    if len(password) < 6:
        messagebox.showwarning("Validation Error", "Password must be at least 6 characters long.")
        return

    # Disable login button during processing (safely)
    try:
        if login_btn is not None and login_btn.winfo_exists():
            login_btn.config(state='disabled', text="Logging in...")
        if root is not None and root.winfo_exists():
            root.update()
    except Exception:
        pass

    db = None
    cursor = None
    try:
        db = connect_db()
        if db is None:
            messagebox.showerror("Database Connection Error", "Database connection failed. Please try again later.")
            return

        cursor = db.cursor()
        hashed_pw = hash_password(password)
        
        # Get user details by email
        query = "SELECT id, name, email FROM users WHERE email=%s AND password=%s"
        cursor.execute(query, (email, hashed_pw))
        result = cursor.fetchone()

        if result:
            # Create user data dictionary
            user_data = {
                'id': result[0],
                'name': result[1],
                'email': result[2] if len(result) > 2 else None,
            }
            
            messagebox.showinfo("Login Successful", f"Welcome to Life Manager, {user_data.get('name') or user_data.get('email')}!")
            
            # Launch dashboard
            if launch_dashboard(user_data):
                print(f"✅ Dashboard launched successfully for user: {user_data.get('email')}")
                # Safely close login window after launching dashboard
                try:
                    if root is not None and root.winfo_exists():
                        root.quit()  # Use quit() instead of destroy() for better cleanup
                        root.destroy()
                except Exception:
                    pass
            else:
                messagebox.showerror("Dashboard Error", "Failed to open the dashboard.")
                
        else:
            messagebox.showerror("Login Failed", "Incorrect email or password.")
            # Clear password field
            password_entry.delete(0, tk.END)
            email_entry.focus()

    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An error occurred: {str(e)}")
    finally:
        # Re-enable login button (safely, in case window is closed)
        try:
            if login_btn is not None and login_btn.winfo_exists():
                login_btn.config(state='normal', text="Login")
        except Exception:
            pass
        
        # Clean up database connections
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if db and db.is_connected():
                db.close()
                print("✅ Database connection closed")
        except Exception:
            pass

# === Enter key binding ===
def on_enter(event):
    login()


def run_login_app():
    """Create and run the modernized Login UI."""
    global root, email_entry, password_entry, login_btn

    # --- UI Setup ---
    root = tk.Tk()
    root.title("Login - Life Manager")
    root.geometry("900x600")
    root.configure(bg="#f0f2f5")  # Light grey background
    root.resizable(False, False)

    # Center the window
    root.eval('tk::PlaceWindow . center')

    # --- Main Content Frame (Card Layout) ---
    main_frame = tk.Frame(root, bg="white")
    main_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=480)
    
    # To prevent the frame from shrinking
    main_frame.pack_propagate(False)

    # --- Header ---
    tk.Label(main_frame, text="Welcome Back!",
             font=("Segoe UI", 22, "bold"),
             bg="white", fg="#333").pack(pady=(40, 10))
    tk.Label(main_frame, text="Sign in to continue to Life Manager",
             font=("Segoe UI", 11),
             bg="white", fg="#666").pack(pady=(0, 35))

    # --- Form Fields ---
    form_frame = tk.Frame(main_frame, bg="white")
    form_frame.pack(pady=10, padx=40, fill="x")

    # Email
    email_label = tk.Label(form_frame, text="Email Address", font=("Segoe UI", 10), bg="white", fg="#555")
    email_label.pack(anchor="w", pady=(0, 5))
    
    email_entry = tk.Entry(form_frame, font=("Segoe UI", 12), width=30, relief="solid", borderwidth=1, bg="#fdfdfe")
    email_entry.pack(ipady=8, fill="x")

    # Password
    password_label = tk.Label(form_frame, text="Password", font=("Segoe UI", 10), bg="white", fg="#555")
    password_label.pack(anchor="w", pady=(15, 5))

    password_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", 12), width=30, relief="solid", borderwidth=1, bg="#fdfdfe")
    password_entry.pack(ipady=8, fill="x")

    # --- Login Button ---
    login_btn = tk.Button(main_frame, text="Login", command=login,
                          bg="#3498db", fg="white", font=("Segoe UI", 12, "bold"),
                          relief="flat", cursor="hand2",
                          activebackground="#2980b9", activeforeground="white")
    login_btn.pack(pady=30, ipady=8, fill="x", padx=40)

    # --- Register Link ---
    link_frame = tk.Frame(main_frame, bg="white")
    link_frame.pack(pady=10)

    tk.Label(link_frame, text="Don't have an account?", font=("Segoe UI", 10), bg="white", fg="#7f8c8d").pack(side="left")
    
    register_link = tk.Label(link_frame, text="Register here", font=("Segoe UI", 10, "underline"), bg="white", fg="#3498db", cursor="hand2")
    register_link.pack(side="left", padx=5)
    register_link.bind("<Button-1>", lambda e: open_register())

    # --- Bindings and Focus ---
    root.bind('<Return>', on_enter)
    password_entry.bind('<Return>', on_enter)
    email_entry.bind('<Return>', on_enter)
    email_entry.focus()

    # --- Window Close Handler ---
    def on_closing():
        try:
            if root is not None and root.winfo_exists():
                root.quit()
                root.destroy()
        except Exception:
            pass

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # --- Start the GUI ---
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
    finally:
        try:
            if root is not None and root.winfo_exists():
                root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    run_login_app()
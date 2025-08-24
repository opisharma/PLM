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

# === Dashboard launching function ===
def launch_dashboard(user_data=None):
    """Launch dashboard with user data"""
    try:
        # Method 1: Try to import and run dashboard directly
        try:
            import dashboard
            if hasattr(dashboard, "launch_dashboard"):
                # Try with user_data; if signature doesn't accept it, call without
                try:
                    dashboard.launch_dashboard(user_data)
                except TypeError:
                    dashboard.launch_dashboard()
                return True
            elif hasattr(dashboard, "main"):
                # Try with user_data; if signature doesn't accept it, call without
                try:
                    dashboard.main(user_data)
                except TypeError:
                    dashboard.main()
                return True
        except ImportError:
            pass
        
        # Method 2: Run dashboard as separate process
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_path = os.path.join(script_dir, "dashboard.py")
        
        if os.path.exists(dashboard_path):
            # Pass user data as command line argument if needed
            if user_data:
                subprocess.Popen([
                    sys.executable, dashboard_path, 
                    f"--user_id={user_data.get('id', '')}"
                ], cwd=script_dir)
            else:
                subprocess.Popen([sys.executable, dashboard_path], cwd=script_dir)
            return True
        else:
            messagebox.showerror("Dashboard Error", "Dashboard file 'dashboard.py' not found.")
            return False
            
    except Exception as e:
        messagebox.showerror("Dashboard Error", f"Failed to launch dashboard: {str(e)}")
        return False

def open_register():
    """Open the registration window and close the login window."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        register_path = os.path.join(script_dir, "register.py")
        if os.path.exists(register_path):
            subprocess.Popen([sys.executable, register_path], cwd=script_dir)
            try:
                root.quit()
            except Exception:
                pass
            try:
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

    # Disable login button during processing
    login_btn.config(state='disabled', text="Logging in...")
    root.update()

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
                root.quit()  # Use quit() instead of destroy() for better cleanup
                root.destroy()
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
        # Re-enable login button
        login_btn.config(state='normal', text="Login")
        
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

# === UI Setup ===
root = tk.Tk()
root.title("Login - Life Manager")
root.geometry("640x520")  # Match register.py window size
root.resizable(True, True)
root.configure(bg="#ecf0f1")

# Initial placement; final centering will be applied after layout
root.eval('tk::PlaceWindow . center')

# Header
header_frame = tk.Frame(root, bg="#3498db", height=60)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

tk.Label(header_frame, text="🔐 Life Manager Login", 
         font=("Segoe UI", 18, "bold"), 
         bg="#3498db", fg="white").pack(expand=True)

# Main content
main_frame = tk.Frame(root, bg="#ecf0f1")
main_frame.pack(expand=True, fill="both", padx=40, pady=30)

# Aligned form using grid (labels and inputs on same row)
label_font = ("Segoe UI", 12)
entry_opts = {"font": ("Segoe UI", 12), "width": 30, "relief": "solid", "borderwidth": 1, "bg": "white"}

form = tk.Frame(main_frame, bg="#ecf0f1")
form.pack(fill="x")
form.grid_columnconfigure(0, weight=0)
form.grid_columnconfigure(1, weight=0)

# Email row
tk.Label(form, text="Email:", font=label_font, bg="#ecf0f1").grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
email_entry = tk.Entry(form, **entry_opts)
email_entry.grid(row=0, column=1, sticky="w", pady=6, ipady=4)

# Password row
tk.Label(form, text="Password:", font=label_font, bg="#ecf0f1").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
password_entry = tk.Entry(form, show="*", **entry_opts)
password_entry.grid(row=1, column=1, sticky="w", pady=(6, 12), ipady=4)

# Login button (packed below the form, like register screen)
login_btn = tk.Button(main_frame, text="Login", command=login,
                     bg="#3498db", fg="white", font=("Segoe UI", 12, "bold"), 
                     width=25, height=2, relief="flat",
                     activebackground="#2980b9", activeforeground="white",
                     cursor="hand2")
login_btn.pack(pady=10)

# Register link row (packed under button)
link_frame = tk.Frame(main_frame, bg="#ecf0f1")
link_frame.pack(pady=6)

link_text = tk.Label(link_frame, text="Don't have an account? ", font=("Segoe UI", 10), bg="#ecf0f1", fg="#7f8c8d")
link_text.pack(side="left")

register_link = tk.Label(link_frame, text="Register here", font=("Segoe UI", 10, "underline"), bg="#ecf0f1", fg="#3498db", cursor="hand2")
register_link.pack(side="left")
register_link.bind("<Button-1>", lambda e: open_register())

# Bind Enter key to login
root.bind('<Return>', on_enter)
password_entry.bind('<Return>', on_enter)
email_entry.bind('<Return>', on_enter)

# Focus on email entry
email_entry.focus()

# Handle window close
def on_closing():
    root.quit()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the GUI
if __name__ == "__main__":
    try:
        # Final centering after layout
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.minsize(360, 420)
        root.mainloop()
    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
    finally:
        try:
            root.destroy()
        except Exception:
            pass
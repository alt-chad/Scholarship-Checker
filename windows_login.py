import tkinter as tk
from tkinter import messagebox
from config import ADMIN_PASSWORD
from ui_widgets import styled_entry

# ── Color palette from brand guide ───────────────────────────────────────────
BURGUNDY = "#3C0016"   # background
BRIGHT_RED = "#F92424"  # primary accent / buttons
SAND = "#D1C0A5"   # primary text
SAND_DIM = "#a89880"   # secondary text
DARK_RED = "#2a0010"   # darker bg for contrast frames


class LoginWindow(tk.Tk):
    """Main login window - entry point of the application."""

    def __init__(self):
        super().__init__()
        self.title("Scholarship Qualification Checker")
        self.geometry("440x350")
        self.resizable(False, False)
        self.configure(bg=BURGUNDY)
        self._build()

    def _build(self):
        tk.Label(self, text="Scholarship",
                 font=("Segoe UI", 22, "bold"),
                 bg=BURGUNDY, fg=SAND).pack(pady=(38, 0))
        tk.Label(self, text="Qualification Checker",
                 font=("Segoe UI", 13),
                 bg=BURGUNDY, fg=BRIGHT_RED).pack()
        tk.Label(self, text="Select your role to continue",
                 font=("Segoe UI", 10),
                 bg=BURGUNDY, fg=SAND_DIM).pack(pady=(6, 30))

        # Student button — Bright Red bg, Sand text
        tk.Button(self,
                  text="  Student  –  Apply for Scholarship  ",
                  bg=BRIGHT_RED, fg=SAND,
                  activebackground="#c91c1c", activeforeground=SAND,
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", cursor="hand2",
                  pady=13,
                  command=self._open_user
                  ).pack(fill="x", padx=70, pady=5)

        # Admin button — Sand bg, Burgundy text
        tk.Button(self,
                  text="  Admin  –  Manage Records  ",
                  bg=SAND, fg=BURGUNDY,
                  activebackground="#bfae94", activeforeground=BURGUNDY,
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", cursor="hand2",
                  pady=13,
                  command=self._open_admin
                  ).pack(fill="x", padx=70, pady=5)

        tk.Label(self, text="Welcome User",
                 font=("Segoe UI", 8),
                 bg=BURGUNDY, fg=SAND_DIM).pack(side="bottom", pady=10)

    def _open_user(self):
        from windows_user import UserWindow
        self.withdraw()
        UserWindow(self)

    def _open_admin(self):
        AdminLoginWindow(self)


class AdminLoginWindow(tk.Toplevel):
    """Admin password gate window."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Admin Login")
        self.geometry("350x240")
        self.resizable(False, False)
        self.configure(bg=BURGUNDY)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Admin Login",
                 font=("Segoe UI", 15, "bold"),
                 bg=BURGUNDY, fg=SAND).pack(pady=(30, 6))
        tk.Label(self, text="Enter admin password:",
                 font=("Segoe UI", 10),
                 bg=BURGUNDY, fg=SAND_DIM).pack()

        self.pw = tk.StringVar()
        e = styled_entry(self, self.pw, width=22, show="*")
        e.pack(pady=12)
        e.bind("<Return>", lambda _: self._login())
        e.focus_set()

        tk.Button(self,
                  text="Login",
                  bg=BRIGHT_RED, fg=SAND,
                  activebackground="#c91c1c", activeforeground=SAND,
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", cursor="hand2",
                  padx=40, pady=9,
                  command=self._login
                  ).pack()

    def _login(self):
        if self.pw.get() == ADMIN_PASSWORD:
            self.destroy()
            self.parent.withdraw()
            from windows_admin import AdminWindow
            AdminWindow(self.parent)
        else:
            messagebox.showerror(
                "Wrong Password", "Incorrect password.", parent=self)
            self.pw.set("")

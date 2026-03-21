import tkinter as tk
from config import BG, BG2, BG3, FG, FG2, FG3


def styled_btn(parent, text, color, cmd, pady=6, padx=14, width=None):
    """Create a styled button with consistent appearance."""
    kw = dict(text=text, bg=color, fg=BG, font=("Segoe UI", 10, "bold"),
              relief="flat", cursor="hand2", pady=pady, padx=padx, command=cmd,
              activebackground=color, activeforeground=BG, bd=0)
    if width:
        kw["width"] = width
    return tk.Button(parent, **kw)


def styled_entry(parent, var, width=28, show=None):
    """Create a styled entry field with consistent appearance."""
    kw = dict(textvariable=var, bg=BG2, fg=FG, insertbackground=FG,
              font=("Segoe UI", 11), relief="flat", bd=6, width=width)
    if show:
        kw["show"] = show
    return tk.Entry(parent, **kw)


def setup_styles():
    """Configure ttk styles for consistent theming across all widgets."""
    from tkinter import ttk
    from config import BLUE, GREEN, YELLOW

    s = ttk.Style()
    s.theme_use("clam")

    # Notebook
    s.configure("TNotebook",        background=BG,  borderwidth=0)
    s.configure("TNotebook.Tab",    background=BG2, foreground=FG,
                padding=[16, 7],    font=("Segoe UI", 10, "bold"))
    s.map("TNotebook.Tab",          background=[("selected", GREEN)],
          foreground=[("selected", BG)])

    # Frame inside notebook
    s.configure("TFrame",           background=BG)

    # Treeview
    s.configure("Treeview",
                background=BG2,
                foreground=FG,
                fieldbackground=BG2,
                rowheight=28,
                font=("Segoe UI", 10),
                borderwidth=0,
                relief="flat")
    s.configure("Treeview.Heading",
                background=BG3,
                foreground=YELLOW,
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                borderwidth=0)
    s.map("Treeview",
          background=[("selected", BLUE)],
          foreground=[("selected", BG)])
    s.map("Treeview.Heading",
          background=[("active", BG3)])

    # Scrollbar
    s.configure("Vertical.TScrollbar",
                background=BG3, troughcolor=BG, borderwidth=0, arrowcolor=FG2)
    s.configure("Horizontal.TScrollbar",
                background=BG3, troughcolor=BG, borderwidth=0, arrowcolor=FG2)

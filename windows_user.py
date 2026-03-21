import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from config import QUALIFIED_FILE, UNQUALIFIED_FILE
from ui_widgets import styled_entry
from file_helpers import load_json, save_json
from scholarship_logic import evaluate
import os

# ── Brand colors ─────────────────────────────────────────────────────────────
_EERIE = "#1a1a1a"
_WHITE = "#ffffff"
_ROSSO = "#D60407"
_DARK = "#0d0d0d"
_DIM = "#aaaaaa"


# ── privacy helpers ──────────────────────────────────────────────────────────

def _mask_name(name: str) -> str:
    parts = name.split()
    masked = []
    for p in parts:
        masked.append(p[0] + "*" * (len(p) - 1) if len(p) > 1 else p)
    return " ".join(masked)


def _mask_id(sid: str) -> str:
    if len(sid) <= 4:
        return "*" * len(sid)
    return sid[:4] + "*" * (len(sid) - 4)


def _mask_email(email: str) -> str:
    if "@" not in email:
        return "****"
    local, domain = email.split("@", 1)
    visible = local[:2] if len(local) >= 2 else local[:1]
    return visible + "*" * max(3, len(local) - 2) + "@" + domain


def _mask_school(sch: str) -> str:
    words = sch.split()
    if len(words) <= 1:
        return sch[0] + "*" * (len(sch) - 1) if len(sch) > 1 else sch
    return words[0] + " " + " ".join("*" * len(w) for w in words[1:])


# ── duplicate check ──────────────────────────────────────────────────────────

def _already_applied(sid: str) -> bool:
    """Returns True if studentID already exists in any file."""
    for filepath in (QUALIFIED_FILE, UNQUALIFIED_FILE):
        for record in load_json(filepath):
            if str(record.get("studentID", "")).strip() == sid.strip():
                return True
    return False


def _duplicate_check(name: str, sid: str) -> str:
    """Returns a warning string if name OR ID matches an existing record, else ''."""
    name_lower = name.strip().lower()
    sid_strip = sid.strip()
    for filepath in (QUALIFIED_FILE, UNQUALIFIED_FILE):
        for record in load_json(filepath):
            same_id = str(record.get("studentID", "")).strip() == sid_strip
            same_name = record.get("name", "").strip().lower() == name_lower
            if same_id and same_name:
                return "⚠ This name + ID already applied!"
            elif same_id and sid_strip:
                return "⚠ This Student ID already applied!"
            elif same_name and name_lower:
                return "⚠ This name already applied!"
    return ""


# ── helper: load & blend bg image ────────────────────────────────────────────

def _load_bg(path: str, w: int, h: int, opacity: int = 170):
    try:
        from PIL import Image, ImageTk
        img = Image.open(path).resize((w, h), Image.LANCZOS)
        overlay = Image.new("RGBA", (w, h), (13, 13, 13, opacity))
        blended = Image.alpha_composite(img.convert("RGBA"), overlay)
        return ImageTk.PhotoImage(blended.convert("RGB"))
    except Exception:
        return None


# ── view-applicants window ────────────────────────────────────────────────────

class ApplicantsWindow(tk.Toplevel):
    COLS = ("Name", "Student ID", "School", "Email")

    def __init__(self, parent):
        super().__init__(parent)
        self.title("All Applicants (Privacy View)")
        self.geometry("820x480")
        self.resizable(True, True)
        self.configure(bg=_EERIE)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=_ROSSO, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Submitted Applicants",
                 font=("Segoe UI", 13, "bold"), bg=_ROSSO, fg=_WHITE).pack()
        tk.Label(hdr, text="Sensitive information is partially hidden for privacy",
                 font=("Segoe UI", 9), bg=_ROSSO, fg=_WHITE).pack()

        body_h = 480 - 60
        bg_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "bg.png")
        self._bg_photo = _load_bg(bg_path, 820, body_h, opacity=160)

        canvas = tk.Canvas(self, width=820, height=body_h,
                           bd=0, highlightthickness=0, bg=_EERIE)
        canvas.pack(fill="both", expand=True)

        if self._bg_photo:
            canvas.create_image(0, 0, anchor="nw", image=self._bg_photo)

        frame = tk.Frame(canvas, bg=_EERIE)
        canvas.create_window(0, 0, anchor="nw", window=frame,
                             width=820, height=body_h - 52)

        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=_DARK, foreground=_WHITE,
                        fieldbackground=_DARK, rowheight=26,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=_EERIE, foreground=_ROSSO,
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", _ROSSO)])

        self.tree = ttk.Treeview(
            frame, columns=self.COLS, show="headings",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set
        )
        col_widths = (160, 110, 220, 240)
        for col, w in zip(self.COLS, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w", minwidth=80)

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True, padx=16, pady=12)

        self._load()

        btn_y = body_h - 48

        self.count_var = tk.StringVar()
        count_lbl = tk.Label(canvas, textvariable=self.count_var,
                             bg=_EERIE, fg=_DIM, font=("Segoe UI", 9))
        canvas.create_window(20, btn_y + 10, anchor="w", window=count_lbl)

        btn_refresh = tk.Button(canvas, text="Refresh",
                                bg=_EERIE, fg=_WHITE,
                                activebackground=_ROSSO, activeforeground=_WHITE,
                                font=("Segoe UI", 9, "bold"), relief="flat",
                                cursor="hand2", pady=6, command=self._load)
        canvas.create_window(640, btn_y, anchor="nw",
                             window=btn_refresh, width=80)

        btn_close = tk.Button(canvas, text="Close",
                              bg=_EERIE, fg=_WHITE,
                              activebackground=_ROSSO, activeforeground=_WHITE,
                              font=("Segoe UI", 9, "bold"), relief="flat",
                              cursor="hand2", pady=6, command=self.destroy)
        canvas.create_window(730, btn_y, anchor="nw",
                             window=btn_close, width=72)

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        all_records = []
        for filepath in (QUALIFIED_FILE, UNQUALIFIED_FILE):
            all_records.extend(load_json(filepath))
        all_records.sort(key=lambda r: r.get(
            "date_submitted", ""), reverse=True)
        for rec in all_records:
            self.tree.insert("", "end", values=(
                _mask_name(rec.get("name", "")),
                _mask_id(str(rec.get("studentID", ""))),
                _mask_school(rec.get("school", "")),
                _mask_email(rec.get("email", "")),
            ))
        self.count_var.set(f"Total applicants: {len(all_records)}")


# ── main user window ──────────────────────────────────────────────────────────

class UserWindow(tk.Toplevel):
    """Student/User scholarship application window."""

    WIN_W = 640
    WIN_H = 860   # increased so all rows + buttons are fully visible

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Student – Scholarship Application")
        self.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.resizable(False, False)
        self.configure(bg=_EERIE)
        self.protocol("WM_DELETE_WINDOW", self._back)
        self._build()

    def _back(self):
        self.destroy()
        self.parent.deiconify()

    def _build(self):
        # ── Red header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=_ROSSO, pady=13)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Scholarship Application Form",
                 font=("Segoe UI", 14, "bold"), bg=_ROSSO, fg=_WHITE).pack()
        tk.Label(hdr, text="Complete all fields then click Submit",
                 font=("Segoe UI", 9), bg=_ROSSO, fg=_WHITE).pack()

        # ── "View All Applicants" always-visible sub-header bar ───────────────
        subhdr = tk.Frame(self, bg=_DARK, pady=7)
        subhdr.pack(fill="x")
        btn_view_top = tk.Button(
            subhdr,
            text="👥  View All Applicants",
            bg=_DARK, fg=_ROSSO,
            activebackground=_EERIE, activeforeground=_ROSSO,
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            command=self._view_applicants
        )
        btn_view_top.pack(side="right", padx=16)

        # ── Canvas body — sized to remaining space ────────────────────────────
        # header ~60px + subheader ~34px = ~94px; leave rest for canvas
        CANVAS_H = self.WIN_H - 94
        bg_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "bg.png")
        self._bg_photo = _load_bg(bg_path, self.WIN_W, CANVAS_H, opacity=140)

        canvas = tk.Canvas(self, width=self.WIN_W, height=CANVAS_H,
                           bd=0, highlightthickness=0, bg=_EERIE)
        # expand=False keeps canvas exact size
        canvas.pack(fill="both", expand=False)

        if self._bg_photo:
            canvas.create_image(0, 0, anchor="nw", image=self._bg_photo)

        # ── Form rows ─────────────────────────────────────────────────────────
        LBL_X = 46
        ENT_X = 240
        START_Y = 28
        ROW_H = 50

        rows = [
            ("Full Name:",                    "v_name"),
            ("Student Id:",                   "v_id"),
            ("School:",                       "v_sch"),
            ("Email:",                        "v_email"),
            ("General Average (0–100):",      "v_avg"),
            ("Lowest Subject Grade (0–100):", "v_low"),
            ("Monthly Family Income (P):",    "v_inc"),
        ]

        # Shared duplicate-warning label (shown under Student Id field)
        dup_warn = tk.Label(canvas, text="", bg=_EERIE, fg="#FF6B00",
                            font=("Segoe UI", 8, "italic"), anchor="w")

        def _refresh_dup_warn(*_):
            msg = _duplicate_check(self.v_name.get(), self.v_id.get())
            dup_warn.config(text=msg)

        for i, (lbl_text, attr) in enumerate(rows):
            y = START_Y + i * ROW_H

            lbl = tk.Label(canvas, text=lbl_text, bg=_EERIE, fg=_WHITE,
                           font=("Segoe UI", 10), anchor="w")
            canvas.create_window(LBL_X, y, anchor="w", window=lbl)

            v = tk.StringVar()
            setattr(self, attr, v)
            ent = styled_entry(canvas, v)
            canvas.create_window(ENT_X, y, anchor="w", window=ent, width=240)

            # ── Student ID: numbers-only + duplicate warning ───────────────
            if attr == "v_id":
                id_warn = tk.Label(canvas, text="", bg=_EERIE, fg=_ROSSO,
                                   font=("Segoe UI", 8, "italic"), anchor="w")
                canvas.create_window(ENT_X, y + 22, anchor="w",
                                     window=id_warn, width=240)
                # Place dup_warn just below the id_warn
                canvas.create_window(ENT_X, y + 36, anchor="w",
                                     window=dup_warn, width=340)

                def _check_id(*_, _v=v, _lbl=id_warn):
                    val = _v.get()
                    if val and not val.isdigit():
                        _lbl.config(text="⚠ Student ID must be numbers only!")
                    else:
                        _lbl.config(text="")
                    _refresh_dup_warn()
                v.trace_add("write", _check_id)

            # ── Full Name: trigger duplicate check on change ───────────────
            elif attr == "v_name":
                v.trace_add("write", _refresh_dup_warn)

            # ── Numeric fields: live type validation ───────────────────────
            elif attr in ("v_avg", "v_low", "v_inc"):
                num_warn = tk.Label(canvas, text="", bg=_EERIE, fg=_ROSSO,
                                    font=("Segoe UI", 8, "italic"), anchor="w")
                canvas.create_window(ENT_X + 245, y, anchor="w",
                                     window=num_warn, width=140)

                def _check_num(*_, _v=v, _lbl=num_warn, _a=attr):
                    val = _v.get().strip()
                    if not val:
                        _lbl.config(text="")
                        return
                    try:
                        num = float(val)
                        if _a in ("v_avg", "v_low") and not (0 <= num <= 100):
                            _lbl.config(text="⚠ Must be 0–100")
                        else:
                            _lbl.config(text="")
                    except ValueError:
                        _lbl.config(text="⚠ Numbers only!")
                v.trace_add("write", _check_num)

        # Extracurricular row
        ext_y = START_Y + len(rows) * ROW_H
        tk.Label(canvas, text="Extracurricular Activities:", bg=_EERIE, fg=_WHITE,
                 font=("Segoe UI", 10), anchor="w").place(x=LBL_X, y=ext_y)
        self.v_extra = tk.BooleanVar()
        tk.Checkbutton(canvas,
                       text="Yes, I participate in extracurricular activities",
                       variable=self.v_extra,
                       bg=_EERIE, fg=_WHITE,
                       activebackground=_EERIE, selectcolor=_DARK,
                       font=("Segoe UI", 10)).place(x=ENT_X, y=ext_y)

        # ── Buttons — anchored from ext_y downward, always visible ───────────
        btn_y = ext_y + 54

        btn_submit = tk.Button(canvas, text="Submit Application",
                               bg=_ROSSO, fg=_WHITE,
                               activebackground="#a80305", activeforeground=_WHITE,
                               font=("Segoe UI", 11, "bold"),
                               relief="flat", cursor="hand2", pady=12,
                               command=self._submit)
        canvas.create_window(46, btn_y, anchor="nw",
                             window=btn_submit, width=548)

        btn_back = tk.Button(canvas, text="Back to Login",
                             bg=_WHITE, fg=_EERIE,
                             activebackground=_DIM, activeforeground=_EERIE,
                             font=("Segoe UI", 10, "bold"),
                             relief="flat", cursor="hand2", pady=7,
                             command=self._back)
        canvas.create_window(46, btn_y + 58, anchor="nw",
                             window=btn_back, width=548)

    # ── view applicants ───────────────────────────────────────────────────────

    def _view_applicants(self):
        ApplicantsWindow(self)

    # ── submit ────────────────────────────────────────────────────────────────

    def _submit(self):
        name = self.v_name.get().strip()
        sid = self.v_id.get().strip()
        sch = self.v_sch.get().strip()
        email = self.v_email.get().strip()
        avg_s = self.v_avg.get().strip()
        low_s = self.v_low.get().strip()
        inc_s = self.v_inc.get().strip()
        extra = self.v_extra.get()

        if not all([name, sid, sch, email, avg_s, low_s, inc_s]):
            messagebox.showwarning(
                "Incomplete", "Please fill in all fields.", parent=self)
            return
        try:
            int(sid)
        except ValueError:
            messagebox.showerror(
                "Invalid", "School ID must contain numbers only.", parent=self)
            return
        try:
            avg = float(avg_s)
            low = float(low_s)
            inc = float(inc_s)
        except ValueError:
            messagebox.showerror(
                "Invalid", "Average, Lowest Grade and Income must be numbers.", parent=self)
            return
        if not (0 <= avg <= 100) or not (0 <= low <= 100):
            messagebox.showerror(
                "Invalid", "Grades must be between 0 and 100.", parent=self)
            return

        dup_msg = _duplicate_check(name, sid)
        if dup_msg:
            messagebox.showerror(
                "Duplicate Application",
                f"{dup_msg.replace('\u26a0 ', '')}\n\n"
                f"Name: {name}\nStudent ID: {sid}\n\n"
                "Each student may only submit one application.",
                parent=self
            )
            return

        qualified, scholarships, reasons_fail = evaluate(
            name, sid, sch, email, avg, low, inc, extra)

        record = {
            "name":                  name,
            "studentID":             sid,
            "school":                sch,
            "email":                 email,
            "average":               avg,
            "lowest_grade":          low,
            "monthly_income":        inc,
            "extracurricular":       extra,
            "date_submitted":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status":                "Qualified" if qualified else "Not Qualified",
            "scholarships_awarded":  scholarships,
            "reasons_not_qualified": reasons_fail,
        }

        if qualified:
            lst = load_json(QUALIFIED_FILE)
            lst.append(record)
            save_json(QUALIFIED_FILE, lst)
            with open("Qualified.txt", "a") as f:
                f.write(
                    f"{name} | {', '.join(scholarships)} | {record['date_submitted']}\n")
        else:
            lst = load_json(UNQUALIFIED_FILE)
            lst.append(record)
            save_json(UNQUALIFIED_FILE, lst)
            with open("Unqualified.txt", "a") as f:
                f.write(
                    f"{name} | Not Qualified | {record['date_submitted']}\n")

        msg = (f"Dear {name},\n\n"
               f"Your scholarship application has been successfully submitted.\n\n"
               f"We will contact you regarding your application status.")
        messagebox.showinfo("Application Submitted", msg, parent=self)

        for a in ("v_name", "v_id", "v_sch", "v_email", "v_avg", "v_low", "v_inc"):
            getattr(self, a).set("")
        self.v_extra.set(False)

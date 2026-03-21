import tkinter as tk
from tkinter import ttk, messagebox
from config import (BG, BG2, BG3, FG, FG2, BLUE, GREEN, RED, ORANGE,
                    QUALIFIED_FILE, UNQUALIFIED_FILE)
from ui_widgets import styled_btn
from file_helpers import load_json, save_json
from scholarship_logic import evaluate


class AdminWindow(tk.Toplevel):
    """Admin panel window for managing student records."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Admin Panel – Scholarship System")
        self.geometry("1050x640")
        self.minsize(800, 500)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._logout)
        self._build()

    def _logout(self):
        self.destroy()
        self.parent.deiconify()

    def _build(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG2, pady=12)
        hdr.pack(fill="x")
        row = tk.Frame(hdr, bg=BG2)
        row.pack()
        tk.Label(row, text="Admin Panel",
                 font=("Segoe UI", 16, "bold"), bg=BG2, fg=FG).pack(side="left")
        tk.Label(row, text="  |  Scholarship Qualification Checker",
                 font=("Segoe UI", 10), bg=BG2, fg=FG2).pack(side="left")

        # ── Notebook ────────────────────────────────────────────────────────
        # Style colored tabs
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=BG2, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background="#11012e",
                        foreground="#ffcc00",
                        font=("Segoe UI", 10, "bold"),
                        padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", "#e8000d"), ("active", "#2a0c62")],
                  foreground=[("selected", "#ffcc00"), ("active", "#ffcc00")])
        # Style treeview heading
        style.configure("Treeview.Heading",
                        background="#e8000d",
                        foreground="#ffcc00",
                        font=("Segoe UI", 9, "bold"),
                        relief="flat")
        style.map("Treeview.Heading",
                  background=[("active", "#b30000")])
        style.configure("Treeview",
                        background="#1e1e2e",
                        foreground="#ffcc00",
                        fieldbackground="#1e1e2e",
                        rowheight=24)
        style.map("Treeview",
                  background=[("selected", "#ffcc00")],
                  foreground=[("selected", "#11012e")])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_q = ttk.Frame(self.nb)
        self.tab_uq = ttk.Frame(self.nb)
        self.tab_c = ttk.Frame(self.nb)

        self.nb.add(self.tab_q,  text="   Qualified Students   ")
        self.nb.add(self.tab_uq, text="   Unqualified Students   ")
        self.nb.add(self.tab_c,  text="   Contact Student   ")

        self._build_student_tab(self.tab_q,  "qualified")
        self._build_student_tab(self.tab_uq, "unqualified")
        self._build_contact_tab()

        self.nb.bind("<<NotebookTabChanged>>", self._on_tab)

        # ── Footer ──────────────────────────────────────────────────────────
        foot = tk.Frame(self, bg=BG2, pady=6)
        foot.pack(fill="x")
        tk.Button(foot, text="Logout",
                  bg="#e8000d", fg="#ffcc00",
                  activebackground="#b30000", activeforeground="#ffcc00",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2",
                  padx=18, pady=5,
                  command=self._logout
                  ).pack(side="right", padx=12)

    def _on_tab(self, _event):
        idx = self.nb.index("current")
        if idx == 0:
            self._reload(self._tree_q, QUALIFIED_FILE)
        elif idx == 1:
            self._reload(self._tree_uq, UNQUALIFIED_FILE)
        elif idx == 2:
            self._reload_contacts()

    # ══════════════════════════════════════════════════════════════════════════
    #  STUDENT TABS  (Qualified / Unqualified)
    # ══════════════════════════════════════════════════════════════════════════
    def _build_student_tab(self, parent, kind):
        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="both", expand=True, padx=8, pady=8)

        bar = tk.Frame(outer, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        styled_btn(bar, "Edit Selected",   BLUE, lambda: self._edit_record(
            kind),   pady=5).pack(side="left", padx=3)
        styled_btn(bar, "Delete Selected", RED, lambda: self._delete_record(
            kind), pady=5).pack(side="left", padx=3)
        styled_btn(bar, "Refresh",         ORANGE, lambda: self._refresh(
            kind),       pady=5).pack(side="left", padx=3)

        cols = (
            "Full Name", "Student Id", "School",
            "General Average", "Lowest Grade", "Monthly Income",
            "Extracurricular", "Date Submitted", "Scholarships/Reason",
        )
        widths = (160, 160, 150, 115, 105, 130, 105, 155, 280)

        tree_frame = tk.Frame(outer, bg=BG)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(tree_frame, columns=cols,
                            show="headings", selectmode="browse")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col, anchor="center")
            tree.column(col, width=w, minwidth=15,
                        anchor="center", stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        tree.tag_configure("odd",  background="#1e1e2e", foreground="#ffcc00")
        tree.tag_configure("even", background="#2a0c62", foreground="#ffffff")

        if kind == "qualified":
            self._tree_q = tree
            self._reload(tree, QUALIFIED_FILE)
        else:
            self._tree_uq = tree
            self._reload(tree, UNQUALIFIED_FILE)

    def _reload(self, tree, filepath):
        tree.delete(*tree.get_children())
        records = load_json(filepath)
        for i, rec in enumerate(records):
            if rec.get("status") == "Qualified":
                detail = ", ".join(rec.get("scholarships_awarded", []))
            else:
                detail = " | ".join(rec.get("reasons_not_qualified", []))

            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end",
                        iid=rec["date_submitted"],
                        tags=(tag,),
                        values=(
                            rec.get("name",           ""),
                            rec.get("studentID",      ""),
                            rec.get("school",         ""),
                            rec.get("average",        ""),
                            rec.get("lowest_grade",   ""),
                            f"P{rec.get('monthly_income', 0):,.2f}",
                            "Yes" if rec.get("extracurricular") else "No",
                            rec.get("date_submitted", ""),
                            detail,
                        ))

    def _refresh(self, kind):
        tree = self._tree_q if kind == "qualified" else self._tree_uq
        fp = QUALIFIED_FILE if kind == "qualified" else UNQUALIFIED_FILE
        self._reload(tree, fp)

    def _get_record(self, kind):
        tree = self._tree_q if kind == "qualified" else self._tree_uq
        sel = tree.selection()
        if not sel:
            messagebox.showinfo(
                "No Selection", "Please select a student record first.", parent=self)
            return None, None, None
        fp = QUALIFIED_FILE if kind == "qualified" else UNQUALIFIED_FILE
        data = load_json(fp)
        rec = next((r for r in data if r["date_submitted"] == sel[0]), None)
        return tree, fp, rec

    def _delete_record(self, kind):
        _, fp, rec = self._get_record(kind)
        if rec is None:
            return
        if not messagebox.askyesno("Confirm", f"Delete record for '{rec['name']}'?", parent=self):
            return
        data = [r for r in load_json(
            fp) if r["date_submitted"] != rec["date_submitted"]]
        save_json(fp, data)
        self._refresh(kind)

    def _edit_record(self, kind):
        _, fp, rec = self._get_record(kind)
        if rec is None:
            return

        from ui_widgets import styled_entry
        dlg = tk.Toplevel(self)
        dlg.title("Edit Record")
        dlg.geometry("420x420")
        dlg.resizable(False, False)
        dlg.configure(bg=BG)
        dlg.grab_set()

        tk.Label(dlg, text="Edit Student Record",
                 font=("Segoe UI", 13, "bold"), bg=BG, fg=FG).pack(pady=(18, 10))

        form = tk.Frame(dlg, bg=BG)
        form.pack(padx=38)

        fields = [
            ("Full Name",    "name",           rec.get("name",           "")),
            ("Student ID",   "studentID",      rec.get("studentID",      "")),
            ("School",       "school",         rec.get("school",         "")),
            ("Average",      "average",        rec.get("average",        "")),
            ("Lowest Grade", "lowest_grade",   rec.get("lowest_grade",   "")),
            ("Income",       "monthly_income", rec.get("monthly_income", "")),
        ]
        fv = {}
        for i, (lbl, key, val) in enumerate(fields):
            tk.Label(form, text=lbl + ":", bg=BG, fg=FG,
                     font=("Segoe UI", 10), anchor="w"
                     ).grid(row=i, column=0, sticky="w", pady=7)
            v = tk.StringVar(value=str(val))
            styled_entry(form, v, width=24).grid(row=i, column=1, padx=14)
            fv[key] = v

        tk.Label(form, text="Extracurricular:", bg=BG, fg=FG,
                 font=("Segoe UI", 10), anchor="w"
                 ).grid(row=6, column=0, sticky="w", pady=7)
        xv = tk.BooleanVar(value=rec.get("extracurricular", False))
        tk.Checkbutton(form, text="Yes", variable=xv,
                       bg=BG, fg=FG, activebackground=BG,
                       selectcolor=BG2, font=("Segoe UI", 10)
                       ).grid(row=6, column=1, sticky="w", padx=14)

        def save():
            try:
                new_name = fv["name"].get().strip()
                new_id = fv["studentID"].get().strip()
                new_sch = fv["school"].get().strip()
                new_avg = float(fv["average"].get())
                new_low = float(fv["lowest_grade"].get())
                new_inc = float(fv["monthly_income"].get())
                new_x = xv.get()
            except ValueError:
                messagebox.showerror(
                    "Error", "Numeric fields must be numbers.", parent=dlg)
                return
            q, sch, fail = evaluate(new_name, new_id, new_sch,
                                    rec.get("email", ""),
                                    new_avg, new_low, new_inc, new_x)
            data = load_json(fp)
            for r in data:
                if r["date_submitted"] == rec["date_submitted"]:
                    r.update({
                        "name": new_name, "studentID": new_id,
                        "school": new_sch, "average": new_avg,
                        "lowest_grade": new_low, "monthly_income": new_inc,
                        "extracurricular": new_x,
                        "scholarships_awarded": sch,
                        "reasons_not_qualified": fail,
                    })
            save_json(fp, data)
            dlg.destroy()
            self._refresh(kind)
            messagebox.showinfo(
                "Saved", f"Record updated for '{new_name}'.", parent=self)

        styled_btn(dlg, "Save Changes", GREEN, save,
                   pady=10, padx=24).pack(pady=20)

    # ══════════════════════════════════════════════════════════════════════════
    #  CONTACT STUDENT TAB
    # ══════════════════════════════════════════════════════════════════════════
    def _build_contact_tab(self):
        outer = tk.Frame(self.tab_c, bg=BG)
        outer.pack(fill="both", expand=True, padx=8, pady=8)

        # ── Toolbar ─────────────────────────────────────────────────────────
        bar = tk.Frame(outer, bg=BG)
        bar.pack(fill="x", pady=(0, 6))
        styled_btn(bar, "Refresh", ORANGE, self._reload_contacts,
                   pady=5).pack(side="left", padx=3)

        # ── Search bar ──────────────────────────────────────────────────────
        search_frame = tk.Frame(outer, bg=BG)
        search_frame.pack(fill="x", pady=(0, 6))

        tk.Label(search_frame, text="Search:", bg=BG, fg=FG,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_contacts())

        search_entry = tk.Entry(
            search_frame,
            textvariable=self._search_var,
            bg=BG2, fg=FG,
            insertbackground=FG,
            relief="flat",
            font=("Segoe UI", 10),
            width=32,
        )
        search_entry.pack(side="left", ipady=5, padx=(0, 6))

        styled_btn(search_frame, "Clear", BG3,
                   lambda: self._search_var.set(""),
                   pady=4, padx=10).pack(side="left")

        # ── Info label ──────────────────────────────────────────────────────
        tk.Label(outer,
                 text="Students who have submitted a scholarship application  •  Click a row to view full details",
                 font=("Segoe UI", 9, "italic"), bg=BG, fg=FG2
                 ).pack(anchor="w", pady=(0, 6))

        # ── Treeview ────────────────────────────────────────────────────────
        cols = ("Full Name", "Email", "Date Submitted")
        widths = (200, 260, 180)

        tree_frame = tk.Frame(outer, bg=BG)
        tree_frame.pack(fill="both", expand=True)

        self._tree_c = ttk.Treeview(tree_frame, columns=cols,
                                    show="headings", selectmode="browse",
                                    cursor="hand2")
        for col, w in zip(cols, widths):
            self._tree_c.heading(col, text=col, anchor="center")
            self._tree_c.column(col, width=w, minwidth=60,
                                anchor="center", stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self._tree_c.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                            command=self._tree_c.xview)
        self._tree_c.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree_c.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self._tree_c.tag_configure("odd",  background="#1e1e2e", foreground="#ffcc00")
        self._tree_c.tag_configure("even", background="#2a0c62", foreground="#ffffff")

        # Bind click → show student info
        self._tree_c.bind("<ButtonRelease-1>", self._on_contact_click)

        # Internal cache of all records for filtering
        self._all_contact_records = []
        self._reload_contacts()

    def _reload_contacts(self):
        """Load all records from both files into the internal cache, then render."""
        all_records = []
        for fp in (QUALIFIED_FILE, UNQUALIFIED_FILE):
            all_records.extend(load_json(fp))
        all_records.sort(key=lambda r: r.get(
            "date_submitted", ""), reverse=True)
        self._all_contact_records = all_records
        # Reset search when reloading
        if hasattr(self, "_search_var"):
            self._search_var.set("")
        self._render_contacts(all_records)

    def _filter_contacts(self):
        """Filter the treeview rows by the current search string."""
        query = self._search_var.get().strip().lower()
        if not query:
            self._render_contacts(self._all_contact_records)
        else:
            filtered = [
                r for r in self._all_contact_records
                if query in r.get("name", "").lower()
            ]
            self._render_contacts(filtered)

    def _render_contacts(self, records):
        """Populate the contact treeview with the given records list."""
        self._tree_c.delete(*self._tree_c.get_children())
        for i, rec in enumerate(records):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree_c.insert("", "end",
                                iid=rec["date_submitted"],
                                tags=(tag,),
                                values=(
                                    rec.get("name",           ""),
                                    rec.get("email",          ""),
                                    rec.get("date_submitted", ""),
                                ))

    def _on_contact_click(self, _event):
        """Open a detail popup when the admin clicks a student row."""
        sel = self._tree_c.selection()
        if not sel:
            return
        date_key = sel[0]
        rec = next(
            (r for r in self._all_contact_records
             if r.get("date_submitted") == date_key),
            None,
        )
        if rec is None:
            return
        self._show_student_info(rec)

    def _show_student_info(self, rec):
        """Display a popup with the full details of the selected student."""
        dlg = tk.Toplevel(self)
        dlg.title(f"Student Info – {rec.get('name', 'Unknown')}")
        dlg.geometry("500x620")
        dlg.minsize(460, 500)
        dlg.resizable(True, True)
        dlg.configure(bg=BG)
        dlg.grab_set()

        # ── Title bar (always visible at top) ──────────────────────────────
        hdr = tk.Frame(dlg, bg=BG2, pady=10)
        hdr.pack(fill="x", side="top")
        tk.Label(hdr, text="Student Information",
                 font=("Segoe UI", 14, "bold"), bg=BG2, fg=FG).pack()

        # ── Bottom buttons (always visible at bottom) ───────────────────────
        btn_frame = tk.Frame(dlg, bg=BG, pady=10)
        btn_frame.pack(fill="x", side="bottom")

        def export_pdf():
            import sys
            import os
            import traceback
            from tkinter import filedialog

            # Make sure the project folder is on the path so pdf_exporter is found
            project_dir = os.path.dirname(os.path.abspath(__file__))
            if project_dir not in sys.path:
                sys.path.insert(0, project_dir)

            safe_name = rec.get("name", "student").replace(" ", "_")
            default_filename = f"StudentInfo_{safe_name}.pdf"

            # Lift dialog to front before opening file chooser
            dlg.lift()
            dlg.focus_force()

            save_path = filedialog.asksaveasfilename(
                parent=dlg,
                title="Save Student Info as PDF",
                initialfile=default_filename,
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            )
            if not save_path:
                return  # user cancelled

            try:
                from pdf_exporter import export_student_pdf
                export_student_pdf(rec, save_path)
                messagebox.showinfo(
                    "PDF Saved",
                    f"Student info has been saved to:\n{save_path}",
                    parent=dlg,
                )
            except Exception as exc:
                messagebox.showerror(
                    "Export Failed",
                    f"Could not save PDF:\n\n{traceback.format_exc()}",
                    parent=dlg,
                )

        styled_btn(btn_frame, "📄  Export as PDF", GREEN, export_pdf,
                   pady=8, padx=20).pack(side="left", padx=12)
        styled_btn(btn_frame, "Close", BG3, dlg.destroy,
                   pady=8, padx=20).pack(side="right", padx=12)

        # ── Scrollable middle area ──────────────────────────────────────────
        canvas = tk.Canvas(dlg, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(e):
            canvas.itemconfig(inner_id, width=e.width)

        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Mouse-wheel scrolling
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        dlg.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ── Status badge ────────────────────────────────────────────────────
        status = rec.get("status", "Unknown")
        badge_color = GREEN if status == "Qualified" else RED
        tk.Label(inner, text=f"  {status}  ",
                 font=("Segoe UI", 10, "bold"),
                 bg=badge_color, fg="#11012e",
                 relief="flat", padx=6, pady=3
                 ).pack(pady=(14, 0))

        # ── Info grid ───────────────────────────────────────────────────────
        frame = tk.Frame(inner, bg=BG, padx=30)
        frame.pack(fill="x", pady=12)

        def add_row(label, value, row_idx):
            tk.Label(frame, text=label,
                     font=("Segoe UI", 10, "bold"),
                     bg=BG, fg=FG2, anchor="w", width=18
                     ).grid(row=row_idx, column=0, sticky="w", pady=5)
            tk.Label(frame, text=str(value) if value != "" else "—",
                     font=("Segoe UI", 10),
                     bg=BG, fg=FG, anchor="w", wraplength=260, justify="left"
                     ).grid(row=row_idx, column=1, sticky="w", pady=5, padx=(8, 0))

        add_row("Full Name:",       rec.get("name",           ""),  0)
        add_row("Student ID:",      rec.get("studentID",      ""),  1)
        add_row("School:",          rec.get("school",         ""),  2)
        add_row("Email:",           rec.get("email",          ""),  3)
        add_row("General Average:", rec.get("average",        ""),  4)
        add_row("Lowest Grade:",    rec.get("lowest_grade",   ""),  5)
        add_row("Monthly Income:",  f"P{rec.get('monthly_income', 0):,.2f}", 6)
        add_row("Extracurricular:", "Yes" if rec.get(
            "extracurricular") else "No", 7)
        add_row("Date Submitted:",  rec.get("date_submitted", ""),  8)

        # ── Scholarships / Reasons ──────────────────────────────────────────
        tk.Frame(inner, bg=BG3, height=1).pack(fill="x", padx=30, pady=(0, 8))

        if status == "Qualified":
            detail_label = "Scholarships Awarded:"
            detail_val = ", ".join(rec.get("scholarships_awarded", [])) or "—"
            detail_color = GREEN
        else:
            detail_label = "Reasons Not Qualified:"
            raw_reasons = rec.get("reasons_not_qualified", [])
            friendly = []
            for r in raw_reasons:
                rl = r.lower()
                if "average" in rl and "below" in rl:
                    friendly.append(
                        "General average must be at least 85.00 to qualify.")
                elif "lowest" in rl and "below" in rl:
                    friendly.append(
                        "All subject grades must be at least 85.00 — no subject should fall below this.")
                elif "income" in rl and "exceeds" in rl:
                    friendly.append(
                        "Monthly family income must not exceed ₱15,000 to be eligible.")
                elif "full scholarship" in rl:
                    friendly.append(
                        "Full Scholarship requires a general average of at least 95, monthly income of ₱10,000 or below, and active participation in extracurricular activities.")
                else:
                    friendly.append(r)
            detail_val = "\n• ".join(friendly)
            if friendly:
                detail_val = "• " + detail_val
            detail_color = RED
        detail_frame = tk.Frame(inner, bg=BG, padx=30)
        detail_frame.pack(fill="x", pady=(0, 14))
        tk.Label(detail_frame, text=detail_label,
                 font=("Segoe UI", 10, "bold"),
                 bg=BG, fg=detail_color, anchor="w"
                 ).pack(anchor="w")
        tk.Label(detail_frame, text=detail_val,
                 font=("Segoe UI", 10),
                 bg=BG, fg=FG, anchor="w",
                 wraplength=420, justify="left"
                 ).pack(anchor="w", pady=(2, 0))
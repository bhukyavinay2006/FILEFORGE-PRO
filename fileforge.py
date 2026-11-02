import json
import os
import shutil
import tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox, ttk


# ============================================================
#                    FILEFORGE PRO
#              Dynamic File Organizer
# ============================================================

APP_NAME = "FILEFORGE PRO"
CONFIG_FILE = "config.json"
HISTORY_FILE = "fileforge_history.json"


# ============================================================
#                      COLORS
# ============================================================

BG = "#07111F"
SIDEBAR = "#0B1728"
PANEL = "#101F33"
CARD = "#152A43"
CARD_HOVER = "#1C3859"

WHITE = "#F8FAFC"
TEXT = "#E2E8F0"
MUTED = "#94A3B8"

BLUE = "#3B82F6"
CYAN = "#06B6D4"
GREEN = "#22C55E"
PURPLE = "#8B5CF6"
YELLOW = "#F59E0B"
PINK = "#EC4899"
RED = "#EF4444"


# ============================================================
#                  DEFAULT JSON CONFIG
# ============================================================

DEFAULT_CONFIG = {
    "categories": {
        "Images": [
            ".jpg", ".jpeg", ".png", ".gif",
            ".bmp", ".svg", ".webp", ".ico"
        ],

        "Videos": [
            ".mp4", ".mkv", ".avi", ".mov",
            ".wmv", ".flv", ".webm"
        ],

        "Audio": [
            ".mp3", ".wav", ".flac",
            ".aac", ".ogg", ".m4a", ".wma"
        ],

        "Documents": [
            ".pdf", ".doc", ".docx",
            ".txt", ".rtf", ".odt", ".md"
        ],

        "Spreadsheets": [
            ".xls", ".xlsx", ".csv", ".ods"
        ],

        "Presentations": [
            ".ppt", ".pptx", ".odp"
        ],

        "Code": [
            ".py", ".java", ".c", ".cpp",
            ".h", ".hpp", ".js", ".ts",
            ".html", ".css", ".php",
            ".sql", ".json", ".xml"
        ],

        "Archives": [
            ".zip", ".rar", ".7z",
            ".tar", ".gz", ".bz2"
        ],

        "Executables": [
            ".exe", ".msi", ".apk",
            ".bat", ".cmd"
        ],

        "Fonts": [
            ".ttf", ".otf",
            ".woff", ".woff2"
        ],

        "Books": [
            ".epub", ".mobi",
            ".azw", ".azw3"
        ]
    }
}


# ============================================================
#                   JSON FUNCTIONS
# ============================================================

def load_json(filename, default):
    try:
        if os.path.exists(filename):

            with open(
                filename,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

    except (
        json.JSONDecodeError,
        OSError
    ):
        pass

    return default


def save_json(filename, data):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


def initialize_files():

    if not os.path.exists(CONFIG_FILE):

        save_json(
            CONFIG_FILE,
            DEFAULT_CONFIG
        )

    if not os.path.exists(HISTORY_FILE):

        save_json(
            HISTORY_FILE,
            []
        )


# ============================================================
#                    FILE CLASSIFIER
# ============================================================

class FileClassifier:

    def __init__(self):

        self.reload_rules()

    def reload_rules(self):

        config = load_json(
            CONFIG_FILE,
            DEFAULT_CONFIG
        )

        categories = config.get(
            "categories",
            {}
        )

        self.rules = {}

        for category, extensions in categories.items():

            self.rules[category] = {
                str(ext).lower()
                if str(ext).startswith(".")
                else "." + str(ext).lower()
                for ext in extensions
            }

    def classify(self, file_path):

        extension = file_path.suffix.lower()

        for category, extensions in self.rules.items():

            if extension in extensions:

                return category

        return "Others"


# ============================================================
#                    FILE ORGANIZER
# ============================================================

class FileOrganizer:

    def __init__(self):

        self.classifier = FileClassifier()

    # --------------------------------------------------------
    # Scan files
    # --------------------------------------------------------

    def scan(
        self,
        folder,
        recursive=True
    ):

        root = Path(folder)

        if not root.exists():

            return []

        files = []

        if recursive:

            for current, dirs, names in os.walk(root):

                # Do not scan category folders again
                category_names = set(
                    self.classifier.rules.keys()
                )

                dirs[:] = [
                    d for d in dirs
                    if d not in category_names
                ]

                for name in names:

                    path = (
                        Path(current) / name
                    )

                    if path.is_file():

                        files.append(path)

        else:

            for path in root.iterdir():

                if path.is_file():

                    files.append(path)

        return sorted(
            files,
            key=lambda x: x.name.lower()
        )

    # --------------------------------------------------------
    # Create organization plan
    # --------------------------------------------------------

    def create_plan(
        self,
        folder,
        recursive=True
    ):

        root = Path(folder)

        plan = []

        for source in self.scan(
            folder,
            recursive
        ):

            # Do not move application data
            if source.name in {
                CONFIG_FILE,
                HISTORY_FILE
            }:
                continue

            category = self.classifier.classify(
                source
            )

            destination = (
                root /
                category /
                source.name
            )

            # Already organized
            if source.parent == root / category:

                continue

            plan.append({
                "source": source,
                "category": category,
                "destination": destination
            })

        return plan

    # --------------------------------------------------------
    # Prevent duplicate names
    # --------------------------------------------------------

    @staticmethod
    def safe_destination(path):

        if not path.exists():

            return path

        number = 1

        while True:

            new_name = (
                f"{path.stem}_{number}"
                f"{path.suffix}"
            )

            new_path = (
                path.parent /
                new_name
            )

            if not new_path.exists():

                return new_path

            number += 1

    # --------------------------------------------------------
    # Organize
    # --------------------------------------------------------

    def organize(
        self,
        plan,
        progress_callback=None
    ):

        history = load_json(
            HISTORY_FILE,
            []
        )

        moved = 0
        errors = []

        total = len(plan)

        for index, item in enumerate(
            plan,
            start=1
        ):

            try:

                destination = (
                    item["destination"]
                )

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                destination = (
                    self.safe_destination(
                        destination
                    )
                )

                shutil.move(
                    str(item["source"]),
                    str(destination)
                )

                history.append({

                    "time":
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),

                    "source":
                        str(item["source"]),

                    "destination":
                        str(destination),

                    "category":
                        item["category"]
                })

                moved += 1

            except Exception as error:

                errors.append(
                    str(error)
                )

            if progress_callback:

                progress_callback(
                    index,
                    total,
                    moved,
                    len(errors)
                )

        save_json(
            HISTORY_FILE,
            history
        )

        return moved, errors

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    def search(
        self,
        folder,
        keyword,
        recursive=True
    ):

        keyword = keyword.lower()

        results = []

        for path in self.scan(
            folder,
            recursive
        ):

            if keyword in path.name.lower():

                results.append(path)

        return results

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    def statistics(
        self,
        folder,
        recursive=True
    ):

        statistics = {}

        for path in self.scan(
            folder,
            recursive
        ):

            category = (
                self.classifier.classify(
                    path
                )
            )

            statistics[category] = (
                statistics.get(
                    category,
                    0
                ) + 1
            )

        return statistics

    # --------------------------------------------------------
    # Undo
    # --------------------------------------------------------

    def undo_last(self):

        history = load_json(
            HISTORY_FILE,
            []
        )

        if not history:

            return False, "Nothing to undo."

        last = history[-1]

        source = Path(
            last["source"]
        )

        destination = Path(
            last["destination"]
        )

        if not destination.exists():

            return False, (
                "The moved file no longer exists."
            )

        try:

            source.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            shutil.move(
                str(destination),
                str(source)
            )

            history.pop()

            save_json(
                HISTORY_FILE,
                history
            )

            return True, (
                f"Restored: {source.name}"
            )

        except Exception as error:

            return False, str(error)


# ============================================================
#                    MAIN APPLICATION
# ============================================================

class FileForgeApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            APP_NAME
        )

        self.root.geometry(
            "1350x820"
        )

        self.root.minsize(
            1050,
            680
        )

        self.root.configure(
            bg=BG
        )

        self.folder = ""

        self.recursive = tk.BooleanVar(
            value=True
        )

        self.organizer = FileOrganizer()

        self.setup_style()

        self.create_sidebar()

        self.create_header()

        self.content = tk.Frame(
            self.root,
            bg=BG
        )

        self.content.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(0, 25)
        )

        self.show_dashboard()

    # ========================================================
    #                    STYLE
    # ========================================================

    def setup_style(self):

        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )
        except:
            pass

        style.configure(
            "Forge.Treeview",

            background=CARD,

            fieldbackground=CARD,

            foreground=TEXT,

            rowheight=34,

            borderwidth=0,

            font=(
                "Segoe UI",
                9
            )
        )

        style.configure(
            "Forge.Treeview.Heading",

            background=CARD_HOVER,

            foreground=WHITE,

            relief="flat",

            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

        style.map(
            "Forge.Treeview",

            background=[
                (
                    "selected",
                    "#315C99"
                )
            ],

            foreground=[
                (
                    "selected",
                    WHITE
                )
            ]
        )

        style.configure(
            "Forge.Horizontal.TProgressbar",

            troughcolor="#243852",

            background=GREEN,

            bordercolor="#243852",

            lightcolor=GREEN,

            darkcolor=GREEN
        )

    # ========================================================
    #                   CLEAR CONTENT
    # ========================================================

    def clear_content(self):

        for widget in (
            self.content.winfo_children()
        ):

            widget.destroy()

    # ========================================================
    #                    CARD
    # ========================================================

    def card(self, parent):

        return tk.Frame(

            parent,

            bg=CARD,

            highlightbackground="#243B59",

            highlightthickness=1
        )

    # ========================================================
    #                 COLOR BUTTON
    # ========================================================

    def button(
        self,
        parent,
        text,
        command,
        color,
        width=15
    ):

        button = tk.Button(

            parent,

            text=text,

            command=command,

            bg=color,

            fg=WHITE,

            activebackground=color,

            activeforeground=WHITE,

            relief="flat",

            bd=0,

            cursor="hand2",

            font=(
                "Segoe UI",
                9,
                "bold"
            ),

            width=width,

            pady=10
        )

        return button

    # ========================================================
    #                    SIDEBAR
    # ========================================================

    def create_sidebar(self):

        sidebar = tk.Frame(

            self.root,

            bg=SIDEBAR,

            width=245
        )

        sidebar.pack(
            side="left",
            fill="y"
        )

        sidebar.pack_propagate(
            False
        )

        # Logo

        tk.Label(

            sidebar,

            text="◆",

            bg=SIDEBAR,

            fg=CYAN,

            font=(
                "Segoe UI",
                35,
                "bold"
            )

        ).pack(
            pady=(22, 0)
        )

        tk.Label(

            sidebar,

            text="FILEFORGE",

            bg=SIDEBAR,

            fg=WHITE,

            font=(
                "Segoe UI",
                22,
                "bold"
            )

        ).pack()

        tk.Label(

            sidebar,

            text="DYNAMIC FILE ORGANIZER",

            bg=SIDEBAR,

            fg=MUTED,

            font=(
                "Segoe UI",
                7,
                "bold"
            )

        ).pack(
            pady=(0, 28)
        )

        # Navigation

        self.nav_button(
            sidebar,
            "⌂   Dashboard",
            self.show_dashboard,
            BLUE
        )

        self.nav_button(
            sidebar,
            "⚡   Organize Files",
            self.show_organize,
            GREEN
        )

        self.nav_button(
            sidebar,
            "🔎   Search",
            self.show_search,
            CYAN
        )

        self.nav_button(
            sidebar,
            "▦   Statistics",
            self.show_statistics,
            PURPLE
        )

        self.nav_button(
            sidebar,
            "☷   History",
            self.show_history,
            YELLOW
        )

        self.nav_button(
            sidebar,
            "↶   Undo Last",
            self.undo,
            PINK
        )

        self.nav_button(
            sidebar,
            "⚙   JSON Rules",
            self.show_rules,
            BLUE
        )

        # Pipeline title

        tk.Label(

            sidebar,

            text="PROJECT PIPELINE",

            bg=SIDEBAR,

            fg="#617994",

            font=(
                "Segoe UI",
                7,
                "bold"
            )

        ).pack(
            anchor="w",
            padx=20,
            pady=(28, 8)
        )

        pipeline = [

            ("01", "Scanner", BLUE),

            ("02", "Classification", PURPLE),

            ("03", "Rule Engine", YELLOW),

            ("04", "Action Executor", GREEN),

            ("05", "Log & Report", CYAN)
        ]

        for number, name, color in pipeline:

            row = tk.Frame(
                sidebar,
                bg=SIDEBAR
            )

            row.pack(
                fill="x",
                padx=20,
                pady=2
            )

            tk.Label(
                row,
                text=number,
                bg=SIDEBAR,
                fg=color,
                font=(
                    "Consolas",
                    8,
                    "bold"
                )
            ).pack(
                side="left"
            )

            tk.Label(
                row,
                text=name,
                bg=SIDEBAR,
                fg=MUTED,
                font=(
                    "Segoe UI",
                    8
                )
            ).pack(
                side="left",
                padx=8
            )

        # Exit

        tk.Button(

            sidebar,

            text="✕   EXIT",

            command=self.root.destroy,

            bg=SIDEBAR,

            fg=RED,

            activebackground=CARD_HOVER,

            activeforeground=WHITE,

            relief="flat",

            bd=0,

            cursor="hand2",

            font=(
                "Segoe UI",
                9,
                "bold"
            )

        ).pack(
            side="bottom",
            fill="x",
            padx=10,
            pady=12
        )

    # ========================================================
    #                 NAVIGATION BUTTON
    # ========================================================

    def nav_button(
        self,
        parent,
        text,
        command,
        color
    ):

        button = tk.Button(

            parent,

            text=text,

            command=command,

            anchor="w",

            bg=SIDEBAR,

            fg=MUTED,

            activebackground=CARD_HOVER,

            activeforeground=WHITE,

            relief="flat",

            bd=0,

            cursor="hand2",

            font=(
                "Segoe UI",
                10,
                "bold"
            ),

            padx=20,

            pady=10
        )

        button.pack(
            fill="x",
            pady=1
        )

        def enter(event):

            button.configure(
                bg=CARD_HOVER,
                fg=WHITE
            )

        def leave(event):

            button.configure(
                bg=SIDEBAR,
                fg=MUTED
            )

        button.bind(
            "<Enter>",
            enter
        )

        button.bind(
            "<Leave>",
            leave
        )

    # ========================================================
    #                    HEADER
    # ========================================================

    def create_header(self):

        header = tk.Frame(
            self.root,
            bg=BG,
            height=95
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        left = tk.Frame(
            header,
            bg=BG
        )

        left.pack(
            side="left",
            padx=28,
            pady=16
        )

        self.title_label = tk.Label(

            left,

            text="FileForge Dashboard",

            bg=BG,

            fg=WHITE,

            font=(
                "Segoe UI",
                24,
                "bold"
            )
        )

        self.title_label.pack(
            anchor="w"
        )

        self.subtitle_label = tk.Label(

            left,

            text="Dynamic file organization system",

            bg=BG,

            fg=MUTED,

            font=(
                "Segoe UI",
                9
            )
        )

        self.subtitle_label.pack(
            anchor="w"
        )

        self.folder_label = tk.Label(

            header,

            text="No folder selected",

            bg=BG,

            fg=MUTED,

            font=(
                "Segoe UI",
                8
            )
        )

        self.folder_label.pack(
            side="right",
            padx=10
        )

        self.button(

            header,

            "📁 SELECT FOLDER",

            self.select_folder,

            BLUE,

            17

        ).pack(
            side="right",
            padx=10,
            pady=24
        )

    # ========================================================
    #                  PIPELINE DISPLAY
    # ========================================================

    def pipeline_display(self):

        frame = tk.Frame(
            self.content,
            bg=BG
        )

        frame.pack(
            fill="x",
            pady=(0, 12)
        )

        stages = [

            ("01", "SCAN", "Find files", BLUE),

            ("02", "CLASSIFY", "Detect type", PURPLE),

            ("03", "RULE", "Choose folder", YELLOW),

            ("04", "ACTION", "Move safely", GREEN),

            ("05", "REPORT", "Save JSON", CYAN)
        ]

        for i, (
            number,
            title,
            description,
            color
        ) in enumerate(stages):

            frame.grid_columnconfigure(
                i,
                weight=1
            )

            box = self.card(
                frame
            )

            box.grid(
                row=0,
                column=i,
                sticky="ew",
                padx=3
            )

            tk.Label(

                box,

                text=f"{number}  ●",

                bg=CARD,

                fg=color,

                font=(
                    "Segoe UI",
                    10,
                    "bold"
                )

            ).pack(
                pady=(9, 0)
            )

            tk.Label(

                box,

                text=title,

                bg=CARD,

                fg=WHITE,

                font=(
                    "Segoe UI",
                    8,
                    "bold"
                )

            ).pack()

            tk.Label(

                box,

                text=description,

                bg=CARD,

                fg=MUTED,

                font=(
                    "Segoe UI",
                    7
                )

            ).pack(
                pady=(0, 9)
            )

    # ========================================================
    #                   DASHBOARD
    # ========================================================

    def show_dashboard(self):

        self.clear_content()

        self.title_label.configure(
            text="FileForge Dashboard"
        )

        self.subtitle_label.configure(
            text="Dynamic File Organizer • Smart Classification • Safe File Management"
        )

        self.pipeline_display()

        if not self.folder:

            self.empty_state(
                "◆",
                "Welcome to FileForge",
                "Select a folder to start organizing your files."
            )

            return

        stats = self.organizer.statistics(
            self.folder,
            self.recursive.get()
        )

        total = sum(
            stats.values()
        )

        row = tk.Frame(
            self.content,
            bg=BG
        )

        row.pack(
            fill="x",
            pady=(0, 12)
        )

        cards = [

            ("▣", "TOTAL FILES",
             total, BLUE),

            ("◆", "IMAGES",
             stats.get("Images", 0),
             PURPLE),

            ("▤", "DOCUMENTS",
             stats.get("Documents", 0),
             CYAN),

            ("♪", "AUDIO",
             stats.get("Audio", 0),
             YELLOW),

            ("▶", "VIDEOS",
             stats.get("Videos", 0),
             GREEN)
        ]

        for i, (
            icon,
            name,
            value,
            color
        ) in enumerate(cards):

            row.grid_columnconfigure(
                i,
                weight=1
            )

            box = self.card(
                row
            )

            box.grid(
                row=0,
                column=i,
                sticky="ew",
                padx=3
            )

            tk.Label(
                box,
                text=icon,
                bg=CARD,
                fg=color,
                font=(
                    "Segoe UI",
                    19,
                    "bold"
                )
            ).pack(
                pady=(10, 0)
            )

            tk.Label(
                box,
                text=str(value),
                bg=CARD,
                fg=WHITE,
                font=(
                    "Segoe UI",
                    23,
                    "bold"
                )
            ).pack()

            tk.Label(
                box,
                text=name,
                bg=CARD,
                fg=MUTED,
                font=(
                    "Segoe UI",
                    8,
                    "bold"
                )
            ).pack(
                pady=(0, 10)
            )

        # Main welcome card

        main = self.card(
            self.content
        )

        main.pack(
            fill="both",
            expand=True
        )

        tk.Label(

            main,

            text="READY TO FORGE YOUR FILES?",

            bg=CARD,

            fg=WHITE,

            font=(
                "Segoe UI",
                23,
                "bold"
            )

        ).pack(
            pady=(50, 8)
        )

        tk.Label(

            main,

            text=(
                "Preview your files first, then organize them "
                "automatically using JSON-based rules."
            ),

            bg=CARD,

            fg=MUTED,

            font=(
                "Segoe UI",
                10
            )

        ).pack()

        buttons = tk.Frame(
            main,
            bg=CARD
        )

        buttons.pack(
            pady=28
        )

        self.button(
            buttons,
            "👀 PREVIEW",
            self.preview,
            YELLOW,
            18
        ).pack(
            side="left",
            padx=5
        )

        self.button(
            buttons,
            "⚡ ORGANIZE NOW",
            self.organize,
            GREEN,
            18
        ).pack(
            side="left",
            padx=5
        )

    # ========================================================
    #                  SELECT FOLDER
    # ========================================================

    def select_folder(self):

        folder = filedialog.askdirectory(
            title="Select Folder for FileForge"
        )

        if folder:

            self.folder = folder

            self.folder_label.configure(
                text=folder
            )

            self.show_dashboard()

    # ========================================================
    #                  ORGANIZE PAGE
    # ========================================================

    def show_organize(self):

        self.clear_content()

        self.title_label.configure(
            text="Organize Files"
        )

        self.subtitle_label.configure(
            text="Preview and safely organize files into smart categories"
        )

        self.pipeline_display()

        if not self.folder:

            self.empty_state(
                "📁",
                "Folder Required",
                "Select a folder before organizing."
            )

            return

        top = self.card(
            self.content
        )

        top.pack(
            fill="x",
            pady=(0, 10)
        )

        tk.Label(

            top,

            text="SOURCE FOLDER",

            bg=CARD,

            fg=MUTED,

            font=(
                "Segoe UI",
                8,
                "bold"
            )

        ).pack(
            anchor="w",
            padx=16,
            pady=(12, 2)
        )

        tk.Label(

            top,

            text=self.folder,

            bg=CARD,

            fg=WHITE,

            font=(
                "Segoe UI",
                9
            )

        ).pack(
            anchor="w",
            padx=16
        )

        controls = tk.Frame(
            top,
            bg=CARD
        )

        controls.pack(
            fill="x",
            padx=16,
            pady=12
        )

        tk.Checkbutton(

            controls,

            text="Scan subfolders",

            variable=self.recursive,

            bg=CARD,

            fg=WHITE,

            selectcolor=CARD_HOVER,

            activebackground=CARD,

            activeforeground=WHITE,

            font=(
                "Segoe UI",
                9
            )

        ).pack(
            side="left"
        )

        self.button(

            controls,

            "⚡ ORGANIZE",

            self.organize,

            GREEN,
            13

        ).pack(
            side="right",
            padx=3
        )

        self.button(

            controls,

            "👀 PREVIEW",

            self.preview,

            YELLOW,
            13

        ).pack(
            side="right",
            padx=3
        )

        plan = self.organizer.create_plan(
            self.folder,
            self.recursive.get()
        )

        tk.Label(

            self.content,

            text=(
                f"{len(plan)} file(s) ready for organization"
            ),

            bg=BG,

            fg=MUTED,

            font=(
                "Segoe UI",
                9,
                "bold"
            )

        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        self.plan_table(
            plan
        )

    # ========================================================
    #                    PLAN TABLE
    # ========================================================

    def plan_table(self, plan):

        box = self.card(
            self.content
        )

        box.pack(
            fill="both",
            expand=True
        )

        columns = (
            "file",
            "category",
            "destination"
        )

        tree = ttk.Treeview(

            box,

            columns=columns,

            show="headings",

            style="Forge.Treeview"
        )

        tree.heading(
            "file",
            text="FILE"
        )

        tree.heading(
            "category",
            text="CATEGORY"
        )

        tree.heading(
            "destination",
            text="DESTINATION"
        )

        tree.column(
            "file",
            width=300
        )

        tree.column(
            "category",
            width=150
        )

        tree.column(
            "destination",
            width=600
        )

        scrollbar = ttk.Scrollbar(

            box,

            orient="vertical",

            command=tree.yview
        )

        tree.configure(
            yscrollcommand=scrollbar.set
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        scrollbar.pack(
            side="right",
            fill="y",
            pady=8
        )

        for item in plan:

            tree.insert(

                "",

                "end",

                values=(

                    item["source"].name,

                    item["category"],

                    str(
                        item["destination"]
                    )
                )
            )

    # ========================================================
    #                      PREVIEW
    # ========================================================

    def preview(self):

        if not self.folder:

            messagebox.showwarning(
                "FileForge",
                "Please select a folder first."
            )

            return

        plan = self.organizer.create_plan(
            self.folder,
            self.recursive.get()
        )

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "FileForge - Dry Run"
        )

        window.geometry(
            "1000x650"
        )

        window.configure(
            bg=BG
        )

        tk.Label(

            window,

            text="👀 DRY RUN PREVIEW",

            bg=BG,

            fg=YELLOW,

            font=(
                "Segoe UI",
                23,
                "bold"
            )

        ).pack(
            pady=(20, 3)
        )

        tk.Label(

            window,

            text=(
                "No files will be moved during preview."
            ),

            bg=BG,

            fg=MUTED,

            font=(
                "Segoe UI",
                9
            )

        ).pack(
            pady=(0, 12)
        )

        text = tk.Text(

            window,

            bg=CARD,

            fg=WHITE,

            insertbackground=WHITE,

            relief="flat",

            font=(
                "Consolas",
                9
            ),

            padx=15,

            pady=15
        )

        text.pack(
            fill="both",
            expand=True,
            padx=22
        )

        if not plan:

            text.insert(
                "end",
                "✓ Everything is already organized."
            )

        else:

            for index, item in enumerate(
                plan,
                1
            ):

                text.insert(

                    "end",

                    f"{index:03}  "
                    f"{item['source'].name}\n"

                    f"      TYPE        : "
                    f"{item['category']}\n"

                    f"      DESTINATION : "
                    f"{item['destination']}\n"

                    + "-" * 95
                    + "\n"
                )

        text.configure(
            state="disabled"
        )

        self.button(

            window,

            "CLOSE",

            window.destroy,

            BLUE,

            14

        ).pack(
            pady=12
        )

    # ========================================================
    #                     ORGANIZE
    # ========================================================

    def organize(self):

        if not self.folder:

            messagebox.showwarning(
                "FileForge",
                "Please select a folder first."
            )

            return

        plan = self.organizer.create_plan(
            self.folder,
            self.recursive.get()
        )

        if not plan:

            messagebox.showinfo(
                "FileForge",
                "✓ No files need organization."
            )

            return

        answer = messagebox.askyesno(

            "Confirm Organization",

            (
                f"FileForge found {len(plan)} "
                f"file(s) to organize.\n\n"
                "Do you want to continue?"
            )
        )

        if not answer:

            return

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "FileForge - Processing"
        )

        window.geometry(
            "580x260"
        )

        window.configure(
            bg=BG
        )

        window.transient(
            self.root
        )

        window.grab_set()

        tk.Label(

            window,

            text="⚡ ACTION EXECUTOR",

            bg=BG,

            fg=GREEN,

            font=(
                "Segoe UI",
                21,
                "bold"
            )

        ).pack(
            pady=(30, 6)
        )

        status = tk.Label(

            window,

            text="Starting...",

            bg=BG,

            fg=MUTED,

            font=(
                "Segoe UI",
                9
            )
        )

        status.pack()

        progress = ttk.Progressbar(

            window,

            style=(
                "Forge.Horizontal.TProgressbar"
            ),

            maximum=max(
                1,
                len(plan)
            )
        )

        progress.pack(
            fill="x",
            padx=50,
            pady=28
        )

        def update_progress(
            current,
            total,
            moved,
            errors
        ):

            progress["value"] = current

            status.configure(

                text=(
                    f"Processed {current}/{total}  |  "
                    f"Moved: {moved}  |  "
                    f"Errors: {errors}"
                )
            )

            window.update_idletasks()

        try:

            moved, errors = (
                self.organizer.organize(
                    plan,
                    update_progress
                )
            )

        finally:

            window.grab_release()

            window.destroy()

        messagebox.showinfo(

            "FileForge Complete",

            (
                "✓ ORGANIZATION COMPLETE\n\n"

                f"Files scanned : {len(plan)}\n"
                f"Files moved   : {moved}\n"
                f"Errors        : {len(errors)}\n\n"

                "Operation history saved to:\n"
                "fileforge_history.json"
            )
        )

        self.show_dashboard()

    # ========================================================
    #                      SEARCH
    # ========================================================

    def show_search(self):

        self.clear_content()

        self.title_label.configure(
            text="Search Files"
        )

        self.subtitle_label.configure(
            text="Quickly find files by name"
        )

        if not self.folder:

            self.empty_state(
                "🔎",
                "Folder Required",
                "Select a folder before searching."
            )

            return

        top = self.card(
            self.content
        )

        top.pack(
            fill="x",
            pady=5
        )

        entry = tk.Entry(

            top,

            bg=CARD_HOVER,

            fg=WHITE,

            insertbackground=WHITE,

            relief="flat",

            font=(
                "Segoe UI",
                11
            )
        )

        entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=15,
            pady=15,
            ipady=7
        )

        output = tk.Text(

            self.content,

            bg=CARD,

            fg=WHITE,

            insertbackground=WHITE,

            relief="flat",

            font=(
                "Consolas",
                9
            ),

            padx=15,

            pady=15
        )

        output.pack(
            fill="both",
            expand=True
        )

        def search_now():

            keyword = entry.get().strip()

            if not keyword:

                messagebox.showwarning(
                    "Search",
                    "Enter a file name or keyword."
                )

                return

            results = self.organizer.search(

                self.folder,

                keyword,

                self.recursive.get()
            )

            output.delete(
                "1.0",
                "end"
            )

            output.insert(

                "end",

                f"🔎 SEARCH RESULTS: "
                f"{keyword}\n"

                + "=" * 90
                + "\n\n"
            )

            if not results:

                output.insert(
                    "end",
                    "No matching files found."
                )

            else:

                for index, path in enumerate(
                    results,
                    1
                ):

                    output.insert(
                        "end",
                        f"{index:03}. {path}\n"
                    )

                output.insert(

                    "end",

                    f"\nTotal results: "
                    f"{len(results)}"
                )

        self.button(

            top,

            "🔎 SEARCH",

            search_now,

            CYAN,

            13

        ).pack(
            side="right",
            padx=15
        )

        entry.bind(
            "<Return>",
            lambda event: search_now()
        )

        entry.focus_set()

    # ========================================================
    #                    STATISTICS
    # ========================================================

    def show_statistics(self):

        self.clear_content()

        self.title_label.configure(
            text="File Statistics"
        )

        self.subtitle_label.configure(
            text="Live classification statistics"
        )

        if not self.folder:

            self.empty_state(
                "▦",
                "Folder Required",
                "Select a folder to generate statistics."
            )

            return

        statistics = self.organizer.statistics(

            self.folder,

            self.recursive.get()
        )

        total = sum(
            statistics.values()
        )

        total_card = self.card(
            self.content
        )

        total_card.pack(
            fill="x",
            pady=5
        )

        tk.Label(

            total_card,

            text=str(total),

            bg=CARD,

            fg=BLUE,

            font=(
                "Segoe UI",
                38,
                "bold"
            )

        ).pack(
            pady=(15, 0)
        )

        tk.Label(

            total_card,

            text="TOTAL FILES FOUND",

            bg=CARD,

            fg=MUTED,

            font=(
                "Segoe UI",
                8,
                "bold"
            )

        ).pack(
            pady=(0, 15)
        )

        colors = [
            BLUE,
            PURPLE,
            CYAN,
            YELLOW,
            GREEN,
            PINK
        ]

        for index, (
            category,
            count
        ) in enumerate(

            sorted(
                statistics.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ):

            row = self.card(
                self.content
            )

            row.pack(
                fill="x",
                pady=3
            )

            color = colors[
                index % len(colors)
            ]

            tk.Label(

                row,

                text=category,

                bg=CARD,

                fg=WHITE,

                width=18,

                anchor="w",

                font=(
                    "Segoe UI",
                    9,
                    "bold"
                )

            ).pack(
                side="left",
                padx=15,
                pady=10
            )

            bar = ttk.Progressbar(

                row,

                style=(
                    "Forge.Horizontal.TProgressbar"
                ),

                maximum=max(
                    1,
                    total
                ),

                value=count
            )

            bar.pack(
                side="left",
                fill="x",
                expand=True,
                padx=10
            )

            tk.Label(

                row,

                text=str(count),

                bg=CARD,

                fg=color,

                font=(
                    "Segoe UI",
                    10,
                    "bold"
                )

            ).pack(
                side="right",
                padx=15
            )

    # ========================================================
    #                    HISTORY
    # ========================================================

    def show_history(self):

        self.clear_content()

        self.title_label.configure(
            text="Operation History"
        )

        self.subtitle_label.configure(
            text="JSON log of all successfully moved files"
        )

        box = self.card(
            self.content
        )

        box.pack(
            fill="both",
            expand=True
        )

        columns = (
            "time",
            "category",
            "source",
            "destination"
        )

        tree = ttk.Treeview(

            box,

            columns=columns,

            show="headings",

            style="Forge.Treeview"
        )

        headings = {

            "time": "TIME",

            "category": "CATEGORY",

            "source": "SOURCE",

            "destination": "DESTINATION"
        }

        for column, heading in headings.items():

            tree.heading(
                column,
                text=heading
            )

        tree.column(
            "time",
            width=155
        )

        tree.column(
            "category",
            width=130
        )

        tree.column(
            "source",
            width=370
        )

        tree.column(
            "destination",
            width=470
        )

        scrollbar = ttk.Scrollbar(

            box,

            orient="vertical",

            command=tree.yview
        )

        tree.configure(
            yscrollcommand=scrollbar.set
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        scrollbar.pack(
            side="right",
            fill="y",
            pady=8
        )

        history = load_json(
            HISTORY_FILE,
            []
        )

        for item in reversed(history):

            tree.insert(

                "",

                "end",

                values=(

                    item.get(
                        "time",
                        ""
                    ),

                    item.get(
                        "category",
                        ""
                    ),

                    item.get(
                        "source",
                        ""
                    ),

                    item.get(
                        "destination",
                        ""
                    )
                )
            )

    # ========================================================
    #                       UNDO
    # ========================================================

    def undo(self):

        success, message = (
            self.organizer.undo_last()
        )

        if success:

            messagebox.showinfo(
                "Undo Successful",
                "✓ " + message
            )

        else:

            messagebox.showwarning(
                "Undo",
                message
            )

        self.show_dashboard()

    # ========================================================
    #                     JSON RULES
    # ========================================================

    def show_rules(self):

        self.clear_content()

        self.title_label.configure(
            text="JSON Classification Rules"
        )

        self.subtitle_label.configure(
            text="FileForge uses config.json to decide where files belong"
        )

        info = self.card(
            self.content
        )

        info.pack(
            fill="x",
            pady=5
        )

        tk.Label(

            info,

            text="⚙  RULE ENGINE",

            bg=CARD,

            fg=CYAN,

            font=(
                "Segoe UI",
                12,
                "bold"
            )

        ).pack(
            anchor="w",
            padx=16,
            pady=(13, 3)
        )

        tk.Label(

            info,

            text=(
                "Example: .jpg → Images, "
                ".pdf → Documents, .py → Code"
            ),

            bg=CARD,

            fg=MUTED,

            font=(
                "Segoe UI",
                9
            )

        ).pack(
            anchor="w",
            padx=16,
            pady=(0, 13)
        )

        editor = tk.Text(

            self.content,

            bg=CARD,

            fg=WHITE,

            insertbackground=WHITE,

            relief="flat",

            font=(
                "Consolas",
                10
            ),

            padx=18,

            pady=18
        )

        editor.pack(
            fill="both",
            expand=True
        )

        editor.insert(

            "1.0",

            json.dumps(

                load_json(
                    CONFIG_FILE,
                    DEFAULT_CONFIG
                ),

                indent=4
            )
        )

        editor.configure(
            state="disabled"
        )

    # ========================================================
    #                    EMPTY STATE
    # ========================================================

    def empty_state(
        self,
        icon,
        title,
        message
    ):

        box = self.card(
            self.content
        )

        box.pack(
            fill="both",
            expand=True
        )

        tk.Label(

            box,

            text=icon,

            bg=CARD,

            fg=CYAN,

            font=(
                "Segoe UI",
                44,
                "bold"
            )

        ).pack(
            pady=(80, 8)
        )

        tk.Label(

            box,

            text=title,

            bg=CARD,

            fg=WHITE,

            font=(
                "Segoe UI",
                22,
                "bold"
            )

        ).pack()

        tk.Label(

            box,

            text=message,

            bg=CARD,

            fg=MUTED,

            font=(
                "Segoe UI",
                10
            )

        ).pack(
            pady=8
        )

        self.button(

            box,

            "📁 SELECT FOLDER",

            self.select_folder,

            BLUE,

            18

        ).pack(
            pady=18
        )


# ============================================================
#                         MAIN
# ============================================================

def main():

    initialize_files()

    root = tk.Tk()

    FileForgeApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()
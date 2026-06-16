import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import os
import sys
import re

from clip_fetcher import ClipFetcher
from clip_editor import ClipEditor


STREAMERS = [
    "marlon", "ishowspeed", "yonnajay", "jynxzi", "tylil", "hasanabi",
    "ddg", "xqc", "pokimane", "agent00", "adapt", "yourragegaming",
    "caseoh247", "jasontheween", "n3on", "2xrakai", "rayasianboy",
    "extraemily", "fanum", "plaqueboymax", "cinna", "stableronaldo", "kaicenat"
]

base_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__)
DEFAULT_EDIT_PATH = os.path.join(base_dir, "..", "edited")



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ClipEditor")
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(bg="#0e0e10")

        self.fetcher = None
        self.clips = []
        self.edit_path = os.path.abspath(DEFAULT_EDIT_PATH)

        self._build_ui()
    
    def _safe_filename(self, title: str) -> str:
        # Remove characters invalid on Windows/macOS/Linux
        name = re.sub(r'[\\/*?:"<>|]', "", title)
        # Replace runs of whitespace/dots with a single underscore
        name = re.sub(r'[\s.]+', "_", name)
        # Strip leading/trailing underscores
        name = name.strip("_")
        # Fallback if title was entirely symbols
        if not name:
            name = "clip"
        # Truncate to 200 chars to stay well under OS limits
        return name[:200]

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        pad = {"padx": 20, "pady": 8}

        # Header
        tk.Label(self, text="ClipEditor", font=("Helvetica", 20, "bold"),
                 bg="#0e0e10", fg="#9147ff").pack(pady=(24, 0))
        tk.Label(self, text="Edit & export Twitch clips", font=("Helvetica", 11),
                 bg="#0e0e10", fg="#adadb8").pack(pady=(2, 16))

        # Streamer dropdown
        tk.Label(self, text="Streamer", font=("Helvetica", 10),
                 bg="#0e0e10", fg="#efeff1", anchor="w").pack(fill="x", padx=20)
        self.streamer_var = tk.StringVar()
        dropdown = ttk.Combobox(self, textvariable=self.streamer_var, values=STREAMERS,
                                state="readonly", font=("Helvetica", 12))
        dropdown.pack(fill="x", padx=20, ipady=6)
        dropdown.current(0)

        # Limit row
        limit_frame = tk.Frame(self, bg="#0e0e10")
        limit_frame.pack(fill="x", **pad)
        tk.Label(limit_frame, text="Clips to fetch", font=("Helvetica", 10),
                 bg="#0e0e10", fg="#efeff1").pack(side="left")
        self.limit_var = tk.IntVar(value=5)
        tk.Spinbox(limit_frame, from_=1, to=100, textvariable=self.limit_var,
                   width=4, font=("Helvetica", 11), bg="#18181b", fg="#efeff1",
                   buttonbackground="#18181b", relief="flat",
                   highlightthickness=1, highlightbackground="#3a3a3d").pack(side="right")

        # Output path row
        path_frame = tk.Frame(self, bg="#0e0e10")
        path_frame.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(path_frame, text="Save to", font=("Helvetica", 10),
                 bg="#0e0e10", fg="#efeff1").pack(side="left")
        self.path_label = tk.Label(path_frame, text=self._short_path(self.edit_path),
                                   font=("Helvetica", 9), bg="#0e0e10", fg="#adadb8",
                                   anchor="w", cursor="hand2")
        self.path_label.pack(side="left", padx=(8, 0))
        self.path_label.bind("<Button-1>", lambda e: self._pick_folder())
        tk.Button(path_frame, text="Browse", command=self._pick_folder,
                  font=("Helvetica", 9), bg="#1f1f23", fg="#efeff1",
                  activebackground="#2a2a2f", relief="flat", cursor="hand2",
                  padx=6, pady=2).pack(side="right")

        # Fetch button
        self.fetch_btn = tk.Button(self, text="Fetch Clips", command=self._fetch,
                                   font=("Helvetica", 12, "bold"),
                                   bg="#9147ff", fg="white", activebackground="#772ce8",
                                   activeforeground="white", relief="flat",
                                   cursor="hand2", pady=8)
        self.fetch_btn.pack(fill="x", padx=20)

        # Clip list header
        list_header = tk.Frame(self, bg="#0e0e10")
        list_header.pack(fill="x", padx=20, pady=(14, 2))
        tk.Label(list_header, text="Clips", font=("Helvetica", 10),
                 bg="#0e0e10", fg="#adadb8").pack(side="left")
        tk.Label(list_header, text="Ctrl+click or Shift+click to select multiple",
                 font=("Helvetica", 8), bg="#0e0e10", fg="#555560").pack(side="right")

        # Listbox — extended multi-select
        list_frame = tk.Frame(self, bg="#18181b", highlightthickness=1,
                              highlightbackground="#3a3a3d")
        list_frame.pack(fill="both", expand=True, padx=20)
        self.listbox = tk.Listbox(list_frame, font=("Helvetica", 10),
                                  bg="#18181b", fg="#efeff1",
                                  selectbackground="#9147ff", selectforeground="white",
                                  relief="flat", activestyle="none", bd=0,
                                  selectmode="extended")
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("purple.Horizontal.TProgressbar",
                        troughcolor="#18181b", background="#9147ff",
                        darkcolor="#9147ff", lightcolor="#9147ff",
                        bordercolor="#18181b")
        ttk.Progressbar(self, variable=self.progress_var, maximum=100,
                        style="purple.Horizontal.TProgressbar").pack(
            fill="x", padx=20, pady=(10, 0))

        # Edit button
        self.edit_btn = tk.Button(self, text="✨  Edit Selected",
                                  command=self._edit_selected,
                                  font=("Helvetica", 11, "bold"),
                                  bg="#1f1f23", fg="#efeff1",
                                  activebackground="#2a2a2f", activeforeground="white",
                                  relief="flat", cursor="hand2", pady=8,
                                  state="disabled")
        self.edit_btn.pack(fill="x", padx=20, pady=(8, 4))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status_var, font=("Helvetica", 9),
                 bg="#0e0e10", fg="#adadb8").pack(pady=(0, 12))

    # ------------------------------------------------------------ helpers ---

    def _short_path(self, path):
        home = os.path.expanduser("~")
        return ("~" + path[len(home):]) if path.startswith(home) else path

    def _pick_folder(self):
        folder = filedialog.askdirectory(initialdir=self.edit_path,
                                         title="Select output folder")
        if folder:
            self.edit_path = folder
            self.path_label.config(text=self._short_path(folder))

    def _set_status(self, msg):
        self.status_var.set(msg)

    def _lock(self):
        self.fetch_btn.config(state="disabled")
        self.edit_btn.config(state="disabled")

    def _unlock(self):
        self.fetch_btn.config(state="normal")
        if self.clips:
            self.edit_btn.config(state="normal")

    # --------------------------------------------------------------- fetch --

    def _fetch(self):
        streamer = self.streamer_var.get().strip()
        self._lock()
        self.listbox.delete(0, "end")
        self.progress_var.set(0)
        self._set_status("Connecting…")

        def run():
            try:
                self.fetcher = ClipFetcher()
                self.fetcher.update_broadcaster_ids([streamer])
                self.clips = self.fetcher.fetch_clips(streamer, limit=self.limit_var.get())
                self.after(0, self._populate_clips)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.after(0, lambda: self._set_status("Failed."))
            finally:
                self.after(0, self._unlock)

        threading.Thread(target=run, daemon=True).start()

    def _populate_clips(self):
        for clip in self.clips:
            self.listbox.insert("end", clip["title"])
        self._set_status(f"{len(self.clips)} clips fetched — select clips to edit.")

    # --------------------------------------------------------------- edit ---

    def _edit_selected(self):
        indices = self.listbox.curselection()
        if not indices:
            messagebox.showwarning("Nothing selected", "Select at least one clip first.")
            return

        selected = [self.clips[i] for i in indices]
        total = len(selected)
        os.makedirs(self.edit_path, exist_ok=True)
        self._lock()
        self.progress_var.set(0)

        def run():
            try:
                editor = ClipEditor()

                for i, clip in enumerate(selected):
                    n = i + 1

                    # 1 — resolve the raw stream URL
                    self.after(0, lambda c=clip, n=n:
                               self._set_status(f"[{n}/{total}] Resolving '{c['title']}'…"))
                    clip["unedited_download_url"] = self.fetcher.clip_download_http(clip)

                    # 2 — submit to editor
                    self.after(0, lambda c=clip, n=n:
                               self._set_status(f"[{n}/{total}] Sending '{c['title']}' to editor…"))
                    edit_id = editor.edit_clip(clip)
                    clip["edit_id"] = edit_id

                    # 3 — wait for render
                    self.after(0, lambda c=clip, n=n:
                               self._set_status(f"[{n}/{total}] Rendering '{c['title']}'…"))
                    download_url = editor.wait_for_movie(edit_id)
                    clip["download_url"] = download_url

                    # 4 — save to disk
                    self.after(0, lambda c=clip, n=n:
                               self._set_status(f"[{n}/{total}] Saving '{c['title']}'…"))
                    filename = self._safe_filename(clip["title"]) + ".mp4"
                    filepath = os.path.join(self.edit_path, filename)
                    response = requests.get(download_url, stream=True)
                    response.raise_for_status()
                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    # advance progress bar
                    self.after(0, lambda p=(n / total * 100): self.progress_var.set(p))

                self.after(0, lambda: self._set_status(
                    f"Done! {total} clip(s) saved to {self._short_path(self.edit_path)}"))
                self.after(0, lambda: messagebox.showinfo(
                    "Done", f"{total} clip(s) edited and saved to:\n{self.edit_path}"))

            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Edit failed", str(err)))
                self.after(0, lambda: self._set_status("Edit failed."))
            finally:
                self.after(0, self._unlock)

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
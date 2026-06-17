import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from .classes.clip_fetcher import ClipFetcher
from .globals import STREAMERS


DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.dirname(__file__), "..", "extracted")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ClipFetcher")
        self.geometry("480x540")
        self.resizable(False, False)
        self.configure(bg="#0e0e10")

        self.fetcher = None
        self.clips = []
        self.download_path = os.path.abspath(DEFAULT_DOWNLOAD_PATH)

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 8}

        # Header
        tk.Label(self, text="ClipFetcher", font=("Helvetica", 20, "bold"),
                 bg="#0e0e10", fg="#9147ff").pack(pady=(24, 0))
        tk.Label(self, text="Download Twitch clips", font=("Helvetica", 11),
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
        spin = tk.Spinbox(limit_frame, from_=1, to=100, textvariable=self.limit_var,
                          width=4, font=("Helvetica", 11), bg="#18181b", fg="#efeff1",
                          buttonbackground="#18181b", relief="flat",
                          highlightthickness=1, highlightbackground="#3a3a3d")
        spin.pack(side="right")

        # Download path row
        path_frame = tk.Frame(self, bg="#0e0e10")
        path_frame.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(path_frame, text="Save to", font=("Helvetica", 10),
                 bg="#0e0e10", fg="#efeff1").pack(side="left")
        self.path_label = tk.Label(path_frame, text=self._short_path(self.download_path),
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

        # Clip list
        tk.Label(self, text="Clips", font=("Helvetica", 10),
                 bg="#0e0e10", fg="#adadb8").pack(anchor="w", padx=20, pady=(14, 2))
        list_frame = tk.Frame(self, bg="#18181b", highlightthickness=1,
                              highlightbackground="#3a3a3d")
        list_frame.pack(fill="both", expand=True, padx=20)
        self.listbox = tk.Listbox(list_frame, font=("Helvetica", 10),
                                  bg="#18181b", fg="#efeff1", selectbackground="#9147ff",
                                  selectforeground="white", relief="flat",
                                  activestyle="none", bd=0)
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)

        # Download button
        self.dl_btn = tk.Button(self, text="Download Selected", command=self._download,
                                font=("Helvetica", 11), bg="#1f1f23", fg="#efeff1",
                                activebackground="#2a2a2f", activeforeground="white",
                                relief="flat", cursor="hand2", pady=7, state="disabled")
        self.dl_btn.pack(fill="x", padx=20, pady=(8, 4))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status_var, font=("Helvetica", 9),
                 bg="#0e0e10", fg="#adadb8").pack(pady=(0, 12))

    def _short_path(self, path):
        home = os.path.expanduser("~")
        if path.startswith(home):
            return "~" + path[len(home):]
        return path

    def _pick_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path, title="Select download folder")
        if folder:
            self.download_path = folder
            self.path_label.config(text=self._short_path(folder))
            if self.fetcher:
                self.fetcher.set_download_path(folder)

    def _set_status(self, msg):
        self.status_var.set(msg)

    def _fetch(self):
        streamer = self.streamer_var.get().strip()

        self.fetch_btn.config(state="disabled")
        self.dl_btn.config(state="disabled")
        self.listbox.delete(0, "end")
        self._set_status("Connecting…")

        def run():
            try:
                self.fetcher = ClipFetcher()
                self.fetcher.set_download_path(self.download_path)
                self.fetcher.update_broadcaster_ids([streamer])
                self.clips = self.fetcher.fetch_clips(streamer, limit=self.limit_var.get())
                self.after(0, self._populate_clips)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.after(0, lambda: self._set_status("Failed."))
            finally:
                self.after(0, lambda: self.fetch_btn.config(state="normal"))

        threading.Thread(target=run, daemon=True).start()

    def _populate_clips(self):
        for clip in self.clips:
            self.listbox.insert("end", clip["title"])
        self._set_status(f"{len(self.clips)} clips fetched.")
        if self.clips:
            self.dl_btn.config(state="normal")

    def _download(self):
        idx = self.listbox.curselection()
        if not idx:
            messagebox.showwarning("Nothing selected", "Select a clip first.")
            return

        clip = self.clips[idx[0]]
        self.dl_btn.config(state="disabled")
        self._set_status(f"Downloading '{clip['title']}'…")

        def run():
            try:
                self.fetcher.download_clip(clip)
                self.after(0, lambda: self._set_status(f"Downloaded: {clip['title']}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Download failed", str(e)))
                self.after(0, lambda: self._set_status("Download failed."))
            finally:
                self.after(0, lambda: self.dl_btn.config(state="normal"))

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
"""
GUI frontend for SSN Redactor.

Dark-mode desktop app built with CustomTkinter.
Delegates all processing to ssn_redactor.engine.
"""

from __future__ import annotations

import threading

import customtkinter as ctk
from tkinter import filedialog

from ssn_redactor.engine import (
    Status,
    collect_files,
    process_folder,
    validate_folder,
)


class SSNRedactorApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        self.title("SSN Redactor")
        self.geometry("780x620")
        self.minsize(700, 550)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.folder_path = ctk.StringVar(value="")
        self._processing_lock = threading.Lock()

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(28, 0), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="SSN Redactor",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Scan PDFs & images, redact Social Security Numbers — 100% local",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Folder picker card
        picker = ctk.CTkFrame(self, corner_radius=14)
        picker.grid(row=1, column=0, padx=30, pady=(20, 0), sticky="ew")
        picker.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            picker, text="Folder",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(18, 8), pady=16, sticky="w")

        self.folder_entry = ctk.CTkEntry(
            picker, textvariable=self.folder_path,
            placeholder_text="Select a folder containing PDFs or JPGs...",
            height=38, corner_radius=10, font=ctk.CTkFont(size=13),
        )
        self.folder_entry.grid(row=0, column=1, padx=(0, 8), pady=16, sticky="ew")

        self.browse_btn = ctk.CTkButton(
            picker, text="Browse", width=100, height=38,
            corner_radius=10, font=ctk.CTkFont(size=13),
            command=self._browse_folder,
        )
        self.browse_btn.grid(row=0, column=2, padx=(0, 18), pady=16)

        # Action row
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, padx=30, pady=(16, 0), sticky="ew")
        actions.grid_columnconfigure(1, weight=1)

        self.run_btn = ctk.CTkButton(
            actions, text="  Start Redaction", height=44,
            corner_radius=12, font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_redaction,
        )
        self.run_btn.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            actions, text="", font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        )
        self.status_label.grid(row=0, column=1, padx=(16, 0), sticky="w")

        self.progress = ctk.CTkProgressBar(actions, height=6, corner_radius=3)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.progress.set(0)

        # Results label
        ctk.CTkLabel(
            self, text="Results",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).grid(row=3, column=0, padx=32, pady=(18, 0), sticky="nw")

        # Log
        self.log_box = ctk.CTkTextbox(
            self, corner_radius=14,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word", state="disabled", activate_scrollbars=True,
        )
        self.log_box.grid(row=4, column=0, padx=30, pady=(6, 14), sticky="nsew")

        # Footer
        ctk.CTkLabel(
            self,
            text="All processing runs locally on your computer  |  No data is sent online",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
        ).grid(row=5, column=0, pady=(0, 14))

    # ------------------------------------------------------------ Actions

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory(title="Select folder with PDFs / JPGs")
        if path:
            self.folder_path.set(path)

    def _log(self, msg: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.run_btn.configure(state=state)
        self.browse_btn.configure(state=state)
        self.folder_entry.configure(state="disabled" if running else "normal")
        if running:
            self.progress.configure(mode="indeterminate")
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.configure(mode="determinate")

    def _start_redaction(self) -> None:
        # Prevent double-click launching parallel jobs
        if not self._processing_lock.acquire(blocking=False):
            return

        folder = self.folder_path.get().strip()
        if not folder:
            self._set_status("Please select a folder first.")
            self._processing_lock.release()
            return

        try:
            resolved = validate_folder(folder)
        except ValueError:
            self._set_status("Invalid folder path.")
            self._processing_lock.release()
            return

        files = collect_files(resolved)
        if not files:
            self._set_status("No PDF or JPG files found in that folder.")
            self._processing_lock.release()
            return

        self._clear_log()
        self._set_running(True)
        self._set_status("Processing...")

        thread = threading.Thread(
            target=self._run_batch, args=(str(resolved), files), daemon=True,
        )
        thread.start()

    def _run_batch(self, folder: str, files: list[str]) -> None:
        try:
            def on_progress(name: str, idx: int, total: int) -> None:
                self.after(0, self._set_status, f"[{idx + 1}/{total}] {name}")

            batch = process_folder(folder, on_progress=on_progress)

            for r in batch.results:
                if r.status == Status.ERROR:
                    self.after(0, self._log, f"  [X]  {r.filename}  --  ERROR: {r.error}")
                elif r.status == Status.NO_TEXT:
                    self.after(0, self._log, f"  [!]  {r.filename}  --  no text layer, skipped")
                elif r.ssn_count == 0:
                    self.after(0, self._log, f"  [ok] {r.filename}  --  0 SSNs found")
                else:
                    self.after(0, self._log, f"  [ok] {r.filename}  --  {r.ssn_count} SSN(s) redacted")

            summary = (
                f"\n{'_' * 50}\n"
                f"  Done!  {len(batch.results)} file(s) processed,  "
                f"{batch.total_redacted} SSN(s) redacted"
            )
            if batch.total_errors:
                summary += f",  {batch.total_errors} error(s)"
            summary += f"\n  Output: {batch.output_folder}\n{'_' * 50}"

            self.after(0, self._log, summary)
            self.after(0, self._set_status, f"Done -- {batch.total_redacted} SSN(s) redacted")
        finally:
            self.after(0, self._set_running, False)
            self.after(0, self.progress.set, 1.0)
            self._processing_lock.release()


def main() -> None:
    app = SSNRedactorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

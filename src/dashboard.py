"""Simple Tkinter dashboard for text-to-audio generation."""

from pathlib import Path
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import Config, FileManager
from voiceover import VoiceoverGenerator


class AudioDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text to Voiceover")
        self.root.geometry("760x560")

        self.config = Config("config/config.yaml")
        self.file_manager = FileManager(self.config)
        self.generator = VoiceoverGenerator(self.config)

        self.last_audio_path = None

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self.root, padx=12, pady=12)
        container.pack(fill="both", expand=True)

        title = tk.Label(container, text="Text to Voiceover", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w")

        subtitle = tk.Label(
            container,
            text="Paste text or load a .txt file, then click Generate Voiceover.",
            font=("Segoe UI", 10),
        )
        subtitle.pack(anchor="w", pady=(2, 10))

        tk.Label(container, text="Text Input", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        self.text_box = tk.Text(container, height=18, wrap="word", font=("Segoe UI", 10))
        self.text_box.pack(fill="both", expand=True, pady=(4, 8))

        options_row = tk.Frame(container)
        options_row.pack(fill="x", pady=(0, 8))

        tk.Label(options_row, text="Output Folder (optional):").pack(side="left")
        self.output_id_var = tk.StringVar()
        self.output_id_entry = tk.Entry(options_row, textvariable=self.output_id_var, width=30)
        self.output_id_entry.pack(side="left", padx=(8, 0))

        buttons_row = tk.Frame(container)
        buttons_row.pack(fill="x", pady=(0, 8))

        tk.Button(buttons_row, text="Load .txt File", command=self.load_text_file).pack(side="left")
        tk.Button(buttons_row, text="Generate Voiceover", command=self.generate_voiceover).pack(side="left", padx=(8, 0))
        tk.Button(buttons_row, text="Open Output Folder", command=self.open_output_folder).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(container, textvariable=self.status_var, anchor="w", fg="#1f4e79")
        status_label.pack(fill="x", pady=(4, 0))

    def load_text_file(self):
        path = filedialog.askopenfilename(
            title="Select text file",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            text = Path(path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            messagebox.showerror("Invalid file", "The selected file is not valid UTF-8 text.")
            return
        except Exception as exc:
            messagebox.showerror("Error", f"Could not read file:\n{exc}")
            return

        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text)
        self.status_var.set(f"Loaded file: {path}")

    def generate_voiceover(self):
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Missing text", "Please enter text or load a .txt file first.")
            return

        output_id = self.output_id_var.get().strip() or None
        self.status_var.set("Generating voiceover...")
        self.root.update_idletasks()

        try:
            video_dir = self.file_manager.create_video_directory(output_id)
            script_data = {
                "full_script": text,
                "word_count": len(text.split()),
            }
            result = self.generator.generate_voiceover(script_data, video_dir)
            self.last_audio_path = Path(result["audio_file"])

            self.status_var.set(
                f"Done. Duration: {result['duration_seconds']:.1f}s | File: {self.last_audio_path}"
            )
            messagebox.showinfo(
                "Success",
                f"Voiceover generated successfully.\n\nFile:\n{self.last_audio_path}",
            )
        except Exception as exc:
            self.status_var.set("Generation failed")
            messagebox.showerror("Generation failed", str(exc))

    def open_output_folder(self):
        target = self.last_audio_path.parent if self.last_audio_path else (Path.cwd() / "output")
        try:
            if os.name == "nt":
                os.startfile(str(target))
            else:
                messagebox.showinfo("Output folder", f"Output folder:\n{target}")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open folder:\n{exc}")

    def run(self):
        self.root.mainloop()


def main():
    app = AudioDashboard()
    app.run()


if __name__ == "__main__":
    main()

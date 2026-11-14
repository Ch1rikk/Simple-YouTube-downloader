import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import threading
import os
import shutil

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader (1080p)")
        self.root.geometry("600x350")
        self.root.resizable(False, False)
        
        self.download_history = []
        
        self.setup_ui()
        self.check_ffmpeg()

    def setup_ui(self):
        # Обновлен заголовок
        header = tk.Label(self.root, text="Скачивание видео с YouTube (1080p, H.264)", 
                         font=("Arial", 12, "bold"))
        header.pack(pady=10)

        # Поле для ссылки
        frame_url = tk.Frame(self.root)
        frame_url.pack(fill="x", padx=20, pady=5)
        tk.Label(frame_url, text="Ссылка:").pack(side="left")
        self.url_entry = tk.Entry(frame_url, width=45)
        self.url_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.url_entry.bind('<Return>', lambda e: self.start_download())

        # Поле для папки
        frame_folder = tk.Frame(self.root)
        frame_folder.pack(fill="x", padx=20, pady=5)
        tk.Label(frame_folder, text="Папка:").pack(side="left")
        self.folder_entry = tk.Entry(frame_folder, width=35)
        self.folder_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.browse_btn = tk.Button(frame_folder, text="Обзор", command=self.select_folder)
        self.browse_btn.pack(side="left")

        # Кнопки управления
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(fill="x", padx=20, pady=5)
        
        self.download_btn = tk.Button(frame_buttons, text="Скачать", 
                                      command=self.start_download, width=12, bg="#4CAF50", fg="white")
        self.download_btn.pack(side="left", padx=5)
        
        self.clear_btn = tk.Button(frame_buttons, text="Очистить", 
                                   command=self.clear_fields, width=12)
        self.clear_btn.pack(side="left", padx=5)
        
        self.status_label = tk.Label(frame_buttons, text="Готов к загрузке", fg="blue")
        self.status_label.pack(side="left", padx=15)

        # История скачиваний
        history_frame = tk.LabelFrame(self.root, text="История скачиваний", padx=10, pady=5)
        history_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.history_text = tk.Text(history_frame, height=6, state=tk.DISABLED, wrap=tk.WORD)
        self.history_text.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(history_frame, command=self.history_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.history_text.config(yscrollcommand=scrollbar.set)

    def check_ffmpeg(self):
        if shutil.which('ffmpeg') is None:
            self.status_label.config(text="⚠ FFmpeg не найден!", fg="red")
            messagebox.showwarning("Внимание", 
                "FFmpeg не найден в системе!\n\n"
                "Без него видео и аудио не смогут склеиться.\n"
                "Скачайте FFmpeg и добавьте его в PATH.")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

    def clear_fields(self):
        self.url_entry.delete(0, tk.END)
        self.status_label.config(text="Готов к загрузке", fg="blue")
        self.url_entry.focus()

    def add_to_history(self, filename, success=True):
        self.download_history.append((filename, success))
        self.history_text.config(state=tk.NORMAL)
        status = "✓" if success else "✗"
        self.history_text.insert(tk.END, f"{status} {filename}\n")
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)

    def update_progress(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            self.root.after(0, lambda: self.status_label.config(
                text=f"Скачивание: {percent} | {speed}", 
                fg="black"
            ))
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.status_label.config(
                text="Обработка файла...", 
                fg="orange"
            ))

    def start_download(self):
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()

        if not url:
            messagebox.showerror("Ошибка", "Вставьте ссылку на видео!")
            return
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Ошибка", "Выберите папку для сохранения!")
            return

        self.download_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Подготовка...", fg="black")

        thread = threading.Thread(target=self.download_video, args=(url, folder), daemon=True)
        thread.start()

    def download_video(self, url, folder):
        # Изменено ограничение высоты на 1080p
        ydl_opts = {
            'format': 'bestvideo[height<=1080][vcodec~="^avc1"]+bestaudio[acodec~="^mp4a"]/best[height<=1080][vcodec~="^avc1"]',
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'progress_hooks': [self.update_progress],
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            
            self.root.after(0, lambda: self.status_label.config(text="✓ Успешно скачано!", fg="green"))
            self.root.after(0, lambda: self.add_to_history(os.path.basename(filename), True))
            
            # Автоматически очищаем поле ссылки для следующего видео
            self.root.after(0, lambda: self.url_entry.delete(0, tk.END))
            self.root.after(0, lambda: self.url_entry.focus())
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.status_label.config(text="✗ Ошибка!", fg="red"))
            self.root.after(0, lambda: self.add_to_history(f"Ошибка: {url[:50]}...", False))
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось скачать:\n\n{error_msg}"))
            
        finally:
            self.root.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.clear_btn.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()
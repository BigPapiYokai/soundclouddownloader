import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import yt_dlp


class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, output_folder):
        super().__init__()
        self.url = url
        self.output_folder = output_folder

    def run(self):
        try:
            def hook(d):
                if d['status'] == 'downloading':
                    p = d.get('downloaded_bytes', 0)
                    t = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    if t:
                        percent = int((p / t) * 100)
                        self.progress.emit(percent)
                elif d['status'] == 'finished':
                    self.progress.emit(100)

            ydl_opts = {
                'outtmpl': os.path.join(self.output_folder, '%(title)s.%(ext)s'),
                'format': 'bestaudio/best',
                'quiet': True,
                'progress_hooks': [hook],
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit("✅ Download complete!")

        except Exception as e:
            self.error.emit(str(e))


class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 SoundCloud Downloader")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QLineEdit {
                background-color: #2c2c3c;
                border: 1px solid #3f3f5f;
                border-radius: 6px;
                padding: 6px;
                color: white;
            }
            QPushButton {
                background-color: #6b5bff;
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8c7aff;
            }
            QProgressBar {
                background-color: #2c2c3c;
                border: 1px solid #3f3f5f;
                border-radius: 6px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #6b5bff;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout()

        self.label = QLabel("Enter SoundCloud song URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://soundcloud.com/...")

        self.path_label = QLabel("Save to folder:")
        self.folder_path = QLineEdit()
        self.folder_path.setText(os.path.join(os.getcwd(), "downloads"))
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.select_folder)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        self.download_btn = QPushButton("Download 🎶")
        self.download_btn.clicked.connect(self.start_download)

        layout.addWidget(self.label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.path_label)
        layout.addWidget(self.folder_path)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.download_btn)

        self.setLayout(layout)

        os.makedirs(self.folder_path.text(), exist_ok=True)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.folder_path.setText(folder)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.critical(self, "Error", "Please enter a valid SoundCloud URL.")
            return

        folder = self.folder_path.text().strip()
        if not os.path.isdir(folder):
            QMessageBox.critical(self, "Error", "Invalid download folder.")
            return

        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        self.thread = DownloadThread(url, folder)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.download_complete)
        self.thread.error.connect(self.download_failed)
        self.thread.start()

    def update_progress(self, percent):
        self.progress_bar.setValue(percent)

    def download_complete(self, msg):
        QMessageBox.information(self, "Done", msg)
        self.download_btn.setEnabled(True)

    def download_failed(self, err):
        QMessageBox.critical(self, "Error", f"Download failed:\n{err}")
        self.download_btn.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloaderApp()
    win.show()
    sys.exit(app.exec())

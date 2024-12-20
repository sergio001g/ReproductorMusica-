import sys
import os
import random
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QFileDialog, QListWidget, QSlider, QTreeView, QLabel, QSplitter,
                             QLineEdit, QMenu, QAction, QMessageBox, QProgressBar, QFileSystemModel)
from PyQt5.QtCore import Qt, QUrl, QDir, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from mutagen.id3 import ID3
from mutagen.mp3 import MP3

class MusicPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperSpoty")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet(self.get_stylesheet())
        self.current_playlist = []
        self.current_index = -1
        self.is_playing = False
        self.is_shuffled = False
        self.repeat_mode = 0
        self.initUI()
        self.player = QMediaPlayer()
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.load_playlists()

    def get_stylesheet(self):
        return """
            QWidget {
                background-color: #121212;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #1DB954;
                border: none;
                padding: 10px;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QListWidget, QTreeView {
                background-color: #181818;
                border: none;
                color: #B3B3B3;
            }
            QListWidget::item:selected, QTreeView::item:selected {
                background-color: #282828;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                background: #535353;
                height: 4px;
            }
            QSlider::handle:horizontal {
                background: #1DB954;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QLineEdit {
                background-color: #282828;
                border: none;
                padding: 5px;
                border-radius: 15px;
                color: #ffffff;
            }
            QProgressBar {
                border: none;
                background-color: #535353;
                height: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
            }
        """

    def initUI(self):
        main_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Horizontal)
        self.folder_tree = QTreeView()
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(QDir.homePath())
        self.file_system_model.setNameFilters(['*.mp3', '*.wav'])
        self.file_system_model.setNameFilterDisables(False)
        self.folder_tree.setModel(self.file_system_model)
        self.folder_tree.setRootIndex(self.file_system_model.index(QDir.homePath()))
        self.folder_tree.setAnimated(False)
        self.folder_tree.setIndentation(20)
        self.folder_tree.setSortingEnabled(True)
        self.folder_tree.setColumnWidth(0, 200)
        for i in range(1, 4):
            self.folder_tree.hideColumn(i)
        self.playlist_widget = QListWidget()
        self.playlist_widget.setFont(QFont("Segoe UI", 10))
        splitter.addWidget(self.folder_tree)
        splitter.addWidget(self.playlist_widget)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar canciones...")
        self.search_bar.textChanged.connect(self.search_songs)
        self.current_song_label = QLabel("No se está reproduciendo ninguna canción")
        self.current_song_label.setAlignment(Qt.AlignCenter)
        self.current_song_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.current_song_label.setStyleSheet("color: #1DB954;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.total_time_label = QLabel("0:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        control_layout = QHBoxLayout()
        self.shuffle_button = QPushButton("🔀")
        self.prev_button = QPushButton("⏮")
        self.play_button = QPushButton("▶")
        self.next_button = QPushButton("⏭")
        self.repeat_button = QPushButton("🔁")
        for button in [self.shuffle_button, self.prev_button, self.play_button, self.next_button, self.repeat_button]:
            button.setFixedSize(40, 40)
            button.setFont(QFont("Segoe UI", 14))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider

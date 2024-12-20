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
        self.repeat_mode = 0  # 0: no repeat, 1: repeat all, 2: repeat one
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
        
        # Splitter para dividir el árbol de carpetas y la lista de reproducción
        splitter = QSplitter(Qt.Horizontal)
        
        # Árbol de carpetas
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
        
        # Lista de reproducción
        self.playlist_widget = QListWidget()
        self.playlist_widget.setFont(QFont("Segoe UI", 10))
        
        splitter.addWidget(self.folder_tree)
        splitter.addWidget(self.playlist_widget)
        
        # Barra de búsqueda
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar canciones...")
        self.search_bar.textChanged.connect(self.search_songs)
        
        # Información de la canción actual
        self.current_song_label = QLabel("No se está reproduciendo ninguna canción")
        self.current_song_label.setAlignment(Qt.AlignCenter)
        self.current_song_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.current_song_label.setStyleSheet("color: #1DB954;")
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        
        # Etiquetas de tiempo
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.total_time_label = QLabel("0:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        
        # Controles de reproducción
        control_layout = QHBoxLayout()
        
        self.shuffle_button = QPushButton("🔀")
        self.prev_button = QPushButton("⏮")
        self.play_button = QPushButton("▶")
        self.next_button = QPushButton("⏭")
        self.repeat_button = QPushButton("🔁")
        
        for button in [self.shuffle_button, self.prev_button, self.play_button, self.next_button, self.repeat_button]:
            button.setFixedSize(40, 40)
            button.setFont(QFont("Segoe UI", 14))
        
        # Control de volumen
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        
        control_layout.addStretch()
        control_layout.addWidget(self.shuffle_button)
        control_layout.addWidget(self.prev_button)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.next_button)
        control_layout.addWidget(self.repeat_button)
        control_layout.addStretch()
        control_layout.addWidget(QLabel("🔊"))
        control_layout.addWidget(self.volume_slider)
        
        # Añadir todos los elementos al layout principal
        main_layout.addWidget(self.search_bar)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.current_song_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(time_layout)
        main_layout.addLayout(control_layout)
        
        self.setLayout(main_layout)
        
        # Conectar señales
        self.folder_tree.clicked.connect(self.folder_clicked)
        self.play_button.clicked.connect(self.play_pause)
        self.prev_button.clicked.connect(self.play_previous)
        self.next_button.clicked.connect(self.play_next)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        self.repeat_button.clicked.connect(self.toggle_repeat)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        # Menú contextual para la lista de reproducción
        self.playlist_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_widget.customContextMenuRequested.connect(self.show_playlist_menu)

    def folder_clicked(self, index):
        path = self.file_system_model.filePath(index)
        self.update_playlist(path)

    def update_playlist(self, path):
        self.playlist_widget.clear()
        self.current_playlist.clear()
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(('.mp3', '.wav')):
                        full_path = os.path.join(root, file)
                        self.current_playlist.append(full_path)
                        self.playlist_widget.addItem(file)

    def play_pause(self):
        if self.current_index >= 0:
            if self.player.state() == QMediaPlayer.PlayingState:
                self.player.pause()
                self.play_button.setText("▶")
            else:
                self.player.play()
                self.play_button.setText("⏸")
        elif self.current_playlist:
            self.current_index = 0
            self.play_current_song()

    def play_selected(self):
        self.current_index = self.playlist_widget.currentRow()
        self.play_current_song()

    def play_current_song(self):
        if 0 <= self.current_index < len(self.current_playlist):
            song_path = self.current_playlist[self.current_index]
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(song_path)))
            self.player.play()
            self.play_button.setText("⏸")
            self.update_song_info(song_path)

    def play_previous(self):
        if self.current_playlist:
            self.current_index = (self.current_index - 1) % len(self.current_playlist)
            self.play_current_song()

    def play_next(self):
        if self.current_playlist:
            if self.is_shuffled:
                self.current_index = random.randint(0, len(self.current_playlist) - 1)
            else:
                self.current_index = (self.current_index + 1) % len(self.current_playlist)
            self.play_current_song()

    def toggle_shuffle(self):
        self.is_shuffled = not self.is_shuffled
        self.shuffle_button.setStyleSheet("background-color: #1DB954;" if self.is_shuffled else "")

    def toggle_repeat(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3
        if self.repeat_mode == 0:
            self.repeat_button.setText("🔁")
            self.repeat_button.setStyleSheet("")
        elif self.repeat_mode == 1:
            self.repeat_button.setText("🔁")
            self.repeat_button.setStyleSheet("background-color: #1DB954;")
        else:
            self.repeat_button.setText("🔂")
            self.repeat_button.setStyleSheet("background-color: #1DB954;")

    def set_volume(self, value):
        self.player.setVolume(value)

    def update_song_info(self, song_path):
        try:
            audio = MP3(song_path, ID3=ID3)
            title = audio.get('TIT2', 'Desconocido')
            artist = audio.get('TPE1', 'Desconocido')
            self.current_song_label.setText(f"{title} - {artist}")
        except:
            self.current_song_label.setText(os.path.basename(song_path))

    def media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if self.repeat_mode == 2:  # Repeat One
                self.player.setPosition(0)
                self.player.play()
            elif self.repeat_mode == 1 or self.current_index < len(self.current_playlist) - 1:
                self.play_next()
            else:
                self.player.stop()
                self.play_button.setText("▶")

    def update_position(self, position):
        self.progress_bar.setValue(position)
        self.current_time_label.setText(self.format_time(position))

    def update_duration(self, duration):
        self.progress_bar.setMaximum(duration)
        self.total_time_label.setText(self.format_time(duration))

    def format_time(self, ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"

    def search_songs(self):
        search_text = self.search_bar.text().lower()
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            if search_text in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def show_playlist_menu(self, position):
        menu = QMenu()
        save_playlist_action = QAction("Guardar lista de reproducción", self)
        save_playlist_action.triggered.connect(self.save_playlist)
        menu.addAction(save_playlist_action)
        menu.exec_(self.playlist_widget.mapToGlobal(position))

    def save_playlist(self):
        name, ok = QFileDialog.getSaveFileName(self, "Guardar lista de reproducción", "", "Playlist (*.json)")
        if ok:
            playlist_data = {
                "name": os.path.basename(name),
                "songs": self.current_playlist
            }
            with open(name, "w") as f:
                json.dump(playlist_data, f)

    def load_playlists(self):
        playlists_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlists")
        if not os.path.exists(playlists_dir):
            os.makedirs(playlists_dir)
        for file in os.listdir(playlists_dir):
            if file.endswith(".json"):
                with open(os.path.join(playlists_dir, file), "r") as f:
                    playlist_data = json.load(f)
                    self.add_playlist_to_tree(playlist_data["name"], playlist_data["songs"])

    def add_playlist_to_tree(self, name, songs):
        playlist_item = QTreeViewItem(self.folder_tree, ["Playlists", name])
        for song in songs:
            QTreeViewItem(playlist_item, [os.path.basename(song)])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.play_pause()
        elif event.key() == Qt.Key_Left:
            self.player.setPosition(max(0, self.player.position() - 5000))
        elif event.key() == Qt.Key_Right:
            self.player.setPosition(min(self.player.duration(), self.player.position() + 5000))
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())
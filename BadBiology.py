#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodeCartographer Lab - Genetic Protection Workstation
Interface GUI thème "Bad Biology" pour la protection d'exécutables
"""

import sys
import os
import json
import base64
import hashlib
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QCheckBox, QComboBox, QGroupBox,
    QSpinBox, QTextEdit, QFileDialog, QProgressBar, QTabWidget,
    QScrollArea, QFrame, QGridLayout, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient, QFontDatabase

# Import du module de protection
try:
    from payload_protector import Config, PayloadGenerator, compress_data, derive_key, encrypt_aes_gcm
    PROTECTOR_AVAILABLE = True
except ImportError:
    PROTECTOR_AVAILABLE = False

# ============================================================
# STYLES CSS - THÈME "BAD BIOLOGY"
# ============================================================
STYLESHEET = """
QMainWindow {
    background-color: #0a0f14;
}

QWidget {
    background-color: transparent;
    color: #00ff88;
    font-family: 'Courier New', monospace;
    font-size: 11px;
}

QGroupBox {
    border: 1px solid #00ff88;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: rgba(0, 40, 20, 0.3);
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #00ff88;
    background-color: rgba(0, 20, 10, 0.8);
}

QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #003311, stop:1 #006622);
    border: 1px solid #00ff88;
    border-radius: 3px;
    padding: 8px 15px;
    color: #00ff88;
    font-weight: bold;
}

QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #006622, stop:1 #00aa44);
    border-color: #00ffaa;
}

QPushButton:pressed {
    background-color: #003311;
}

QPushButton:disabled {
    background-color: #1a1a1a;
    border-color: #333333;
    color: #555555;
}

QLabel {
    color: #00ff88;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #00ffaa;
    background-color: rgba(0, 40, 20, 0.5);
    padding: 10px;
    border-radius: 5px;
}

QSlider::groove:horizontal {
    border: 1px solid #00ff88;
    height: 6px;
    background: rgba(0, 40, 20, 0.5);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00ff88, stop:1 #00aa44);
    border: 1px solid #00ff88;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #003311, stop:1 #00ff88);
    border-radius: 3px;
}

QCheckBox {
    spacing: 8px;
    color: #00ff88;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #00ff88;
    border-radius: 3px;
    background-color: rgba(0, 40, 20, 0.5);
}

QCheckBox::indicator:checked {
    background-color: #00ff88;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgM0w0LjUgOC41TDIgNi41IiBzdHJva2U9IiMwMDBhMDAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
}

QComboBox {
    border: 1px solid #00ff88;
    border-radius: 3px;
    padding: 5px 10px;
    background-color: rgba(0, 40, 20, 0.5);
    color: #00ff88;
    min-width: 150px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #0a0f14;
    border: 1px solid #00ff88;
    selection-background-color: #003311;
    color: #00ff88;
}

QSpinBox {
    border: 1px solid #00ff88;
    border-radius: 3px;
    padding: 5px;
    background-color: rgba(0, 40, 20, 0.5);
    color: #00ff88;
}

QSpinBox::up-button, QSpinBox::down-button {
    border: 1px solid #00ff88;
    background-color: rgba(0, 60, 30, 0.5);
    width: 15px;
}

QTextEdit {
    border: 1px solid #00ff88;
    border-radius: 3px;
    background-color: rgba(0, 20, 10, 0.6);
    color: #00ff88;
    font-family: 'Consolas', 'Courier New', monospace;
    selection-background-color: #003311;
}

QProgressBar {
    border: 1px solid #00ff88;
    border-radius: 3px;
    text-align: center;
    background-color: rgba(0, 40, 20, 0.3);
    color: #00ff88;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #003311, stop:0.5 #00ff88, stop:1 #003311);
    border-radius: 2px;
}

QTabWidget::pane {
    border: 1px solid #00ff88;
    border-radius: 5px;
    background-color: rgba(0, 30, 15, 0.3);
}

QTabBar::tab {
    background-color: rgba(0, 40, 20, 0.3);
    border: 1px solid #00ff88;
    border-bottom-color: #00ff88;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 120px;
    padding: 8px;
    color: #00ff88;
}

QTabBar::tab:selected {
    background-color: rgba(0, 60, 30, 0.6);
    border-bottom-color: transparent;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(0, 80, 40, 0.4);
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QFrame#dnaPanel {
    background-color: rgba(0, 30, 15, 0.4);
    border: 2px solid #00ff88;
    border-radius: 10px;
}

QFrame#statusPanel {
    background-color: rgba(0, 40, 20, 0.3);
    border: 1px solid #00aa44;
    border-radius: 5px;
}

/* Animations */
QPushButton#mutateBtn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #330011, stop:1 #660022);
    border-color: #ff0088;
    color: #ff0088;
}

QPushButton#mutateBtn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #660022, stop:1 #aa0044);
    border-color: #ff00aa;
}

QLabel#mutationRate {
    font-size: 18px;
    font-weight: bold;
    color: #ff0088;
    background-color: rgba(50, 0, 20, 0.6);
    padding: 5px;
    border-radius: 3px;
    border: 1px solid #ff0088;
}
"""

# ============================================================
# WIDGET DNA HELIX - VISUALISATION GÉNÉTIQUE
# ============================================================
class DNAHelixWidget(QWidget):
    """Widget affichant une double hélice d'ADN animée"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)
        self.setMinimumWidth(400)
        self.phase = 0
        self.mutation_points = []
        self.lock_icons = []
        
        # Timer pour l'animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)
        
    def update_animation(self):
        self.phase += 0.05
        self.update()
        
    def set_mutation_points(self, points):
        """Définit les points de mutation sur l'ADN"""
        self.mutation_points = points
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_x = width // 2
        
        # Dessiner la double hélice
        amplitude = 80
        frequency = 0.02
        num_points = 100
        
        # Brin 1
        path1 = []
        for i in range(num_points):
            y = (i / num_points) * height
            x = center_x + amplitude * math.sin(2 * math.pi * frequency * y + self.phase)
            path1.append((x, y))
            
        # Brin 2
        path2 = []
        for i in range(num_points):
            y = (i / num_points) * height
            x = center_x + amplitude * math.sin(2 * math.pi * frequency * y + self.phase + math.pi)
            path2.append((x, y))
        
        # Dessiner les brins
        pen = QPen(QColor(0, 255, 136), 3, Qt.SolidLine)
        painter.setPen(pen)
        
        # Brin 1
        for i in range(len(path1) - 1):
            x1, y1 = path1[i]
            x2, y2 = path1[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
        # Brin 2
        for i in range(len(path2) - 1):
            x1, y1 = path2[i]
            x2, y2 = path2[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Dessiner les paires de bases
        painter.setPen(QPen(QColor(0, 200, 100), 1, Qt.SolidLine))
        for i in range(0, num_points, 8):
            x1, y1 = path1[i]
            x2, y2 = path2[i]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Points de connexion brillants
            gradient = QRadialGradient(x1, y1, 5)
            gradient.setColorAt(0, QColor(0, 255, 136, 200))
            gradient.setColorAt(1, QColor(0, 255, 136, 0))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x1) - 3, int(y1) - 3, 6, 6)
            
        # Dessiner les points de mutation
        for point in self.mutation_points:
            y_pos = (point / 100) * height
            x_pos = center_x + amplitude * math.sin(2 * math.pi * frequency * y_pos + self.phase)
            
            # Cercle de mutation
            gradient = QRadialGradient(x_pos, y_pos, 15)
            gradient.setColorAt(0, QColor(255, 0, 136, 255))
            gradient.setColorAt(0.5, QColor(255, 0, 136, 100))
            gradient.setColorAt(1, QColor(255, 0, 136, 0))
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(255, 0, 136), 2))
            painter.drawEllipse(int(x_pos) - 8, int(y_pos) - 8, 16, 16)
            
            # Icône de cadenas
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawText(int(x_pos) - 5, int(y_pos) + 5, "🔒")


# ============================================================
# THREAD DE TRAITEMENT
# ============================================================
class ProtectionThread(QThread):
    """Thread pour le traitement asynchrone"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, exe_path, config_dict):
        super().__init__()
        self.exe_path = exe_path
        self.config_dict = config_dict
        
    def run(self):
        try:
            if not PROTECTOR_AVAILABLE:
                self.error.emit("Module payload_protector non disponible")
                return
                
            self.status.emit("Initialisation du laboratoire...")
            self.progress.emit(10)
            
            # Créer la configuration
            config = Config()
            config.COMPRESSION_ENABLED = self.config_dict.get('compression_enabled', True)
            config.COMPRESSION_ALGORITHM = self.config_dict.get('compression_algo', 'zlib')
            config.COMPRESSION_LEVEL = self.config_dict.get('compression_level', 9)
            config.COMPRESSION_LAYERS = self.config_dict.get('compression_layers', 2)
            config.ENCRYPTION_ENABLED = self.config_dict.get('encryption_enabled', True)
            config.ENCRYPTION_ALGORITHM = self.config_dict.get('encryption_algo', 'aes')
            config.ANTI_DEBUG_ENABLED = self.config_dict.get('anti_debug', True)
            config.ANTI_VM_ENABLED = self.config_dict.get('anti_vm', True)
            config.ANTI_SANDBOX_ENABLED = self.config_dict.get('anti_sandbox', True)
            config.EXECUTION_MODE = self.config_dict.get('execution_mode', 'fileless')
            config.INTEGRITY_CHECK = self.config_dict.get('integrity_check', True)
            config.EXPIRATION_DATE = self.config_dict.get('expiration_date')
            config.VERBOSE = True
            
            self.status.emit("Analyse du génome exécutable...")
            self.progress.emit(30)
            
            # Générer le payload
            generator = PayloadGenerator(config)
            payload_data = generator.process_payload(self.exe_path)
            
            self.status.emit("Mutation génétique en cours...")
            self.progress.emit(60)
            
            # Générer le code C#
            csharp_code = generator.generate_csharp_loader(payload_data)
            
            self.status.emit("Finalisation de la séquence...")
            self.progress.emit(90)
            
            # Préparer les résultats
            result = {
                'payload_data': payload_data,
                'csharp_code': csharp_code,
                'config': config
            }
            
            self.progress.emit(100)
            self.status.emit("Séquence générée avec succès!")
            self.finished_signal.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
# FENÊTRE PRINCIPALE
# ============================================================
class CodeCartographerLab(QMainWindow):
    """Fenêtre principale du laboratoire"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeCartographer Lab - Genetic Protection Workstation")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(STYLESHEET)
        
        self.current_exe_path = None
        self.last_result = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Titre
        title_label = QLabel("🧬 CODECARTOGRAPHER LAB - GENETIC PROTECTION WORKSTATION 🧬")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau gauche - Contrôles
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Panneau droit - Visualisation et code
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Barre de statut
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Prêt à muter le code génétique")
        self.status_bar.addWidget(self.status_label)
        
    def create_left_panel(self):
        """Crée le panneau de contrôle gauche"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        
        # Groupe 1: Fichier exécutable
        file_group = QGroupBox("📁 SÉQUENCE EXÉCUTABLE")
        file_layout = QVBoxLayout()
        
        self.file_label = QLabel("Aucun fichier chargé")
        self.file_label.setStyleSheet("background-color: rgba(0, 30, 15, 0.5); padding: 10px; border-radius: 3px;")
        file_layout.addWidget(self.file_label)
        
        load_btn = QPushButton("🔬 Charger un exécutable")
        load_btn.clicked.connect(self.load_executable)
        file_layout.addWidget(load_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Groupe 2: Compression
        comp_group = QGroupBox("🗜️ COMPRESSION GÉNÉTIQUE")
        comp_layout = QGridLayout()
        
        self.compression_check = QCheckBox("Activer la compression")
        self.compression_check.setChecked(True)
        comp_layout.addWidget(self.compression_check, 0, 0, 1, 2)
        
        comp_layout.addWidget(QLabel("Algorithme:"), 1, 0)
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(['zlib', 'bz2', 'lzma'])
        comp_layout.addWidget(self.compression_combo, 1, 1)
        
        comp_layout.addWidget(QLabel("Niveau (1-9):"), 2, 0)
        self.compression_level = QSpinBox()
        self.compression_level.setRange(1, 9)
        self.compression_level.setValue(9)
        comp_layout.addWidget(self.compression_level, 2, 1)
        
        comp_layout.addWidget(QLabel("Couches:"), 3, 0)
        self.compression_layers = QSpinBox()
        self.compression_layers.setRange(1, 3)
        self.compression_layers.setValue(2)
        comp_layout.addWidget(self.compression_layers, 3, 1)
        
        comp_group.setLayout(comp_layout)
        layout.addWidget(comp_group)
        
        # Groupe 3: Chiffrement
        enc_group = QGroupBox("🔐 CHIFFREMENT QUANTIQUE")
        enc_layout = QGridLayout()
        
        self.encryption_check = QCheckBox("Activer le chiffrement")
        self.encryption_check.setChecked(True)
        enc_layout.addWidget(self.encryption_check, 0, 0, 1, 2)
        
        enc_layout.addWidget(QLabel("Algorithme:"), 1, 0)
        self.encryption_combo = QComboBox()
        self.encryption_combo.addItems(['aes', 'chacha20', 'xor'])
        enc_layout.addWidget(self.encryption_combo, 1, 1)
        
        enc_layout.addWidget(QLabel("Itérations PBKDF2:"), 2, 0)
        self.pbkdf2_iterations = QSpinBox()
        self.pbkdf2_iterations.setRange(10000, 1000000)
        self.pbkdf2_iterations.setSingleStep(50000)
        self.pbkdf2_iterations.setValue(500000)
        enc_layout.addWidget(self.pbkdf2_iterations, 2, 1)
        
        enc_group.setLayout(enc_layout)
        layout.addWidget(enc_group)
        
        # Groupe 4: Anti-Reverse
        anti_group = QGroupBox("🛡️ SYSTÈMES DE DÉFENSE")
        anti_layout = QVBoxLayout()
        
        self.anti_debug = QCheckBox("Anti-Debugging")
        self.anti_debug.setChecked(True)
        anti_layout.addWidget(self.anti_debug)
        
        self.anti_vm = QCheckBox("Anti-VM / Anti-Sandbox")
        self.anti_vm.setChecked(True)
        anti_layout.addWidget(self.anti_vm)
        
        self.integrity_check = QCheckBox("Vérification d'intégrité (HMAC)")
        self.integrity_check.setChecked(True)
        anti_layout.addWidget(self.integrity_check)
        
        anti_group.setLayout(anti_layout)
        layout.addWidget(anti_group)
        
        # Groupe 5: Exécution
        exec_group = QGroupBox("⚡ MODE D'EXÉCUTION")
        exec_layout = QVBoxLayout()
        
        self.execution_mode = QComboBox()
        self.execution_mode.addItems(['fileless', 'standard'])
        exec_layout.addWidget(QLabel("Mode:"))
        exec_layout.addWidget(self.execution_mode)
        
        self.expiration_check = QCheckBox("Date d'expiration")
        self.expiration_check.stateChanged.connect(self.toggle_expiration)
        exec_layout.addWidget(self.expiration_check)
        
        self.expiration_date = QComboBox()
        self.expiration_date.setEnabled(False)
        days = [7, 14, 30, 60, 90, 180, 365]
        for d in days:
            self.expiration_date.addItem(f"{d} jours", d)
        exec_layout.addWidget(self.expiration_date)
        
        exec_group.setLayout(exec_layout)
        layout.addWidget(exec_group)
        
        # Bouton de mutation
        self.mutate_btn = QPushButton("🧬 LANÇER LA MUTATION GÉNÉTIQUE")
        self.mutate_btn.setObjectName("mutateBtn")
        self.mutate_btn.setMinimumHeight(50)
        self.mutate_btn.setFont(QFont("Courier New", 12, QFont.Bold))
        self.mutate_btn.clicked.connect(self.start_mutation)
        layout.addWidget(self.mutate_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return scroll
        
    def create_right_panel(self):
        """Crée le panneau de visualisation droit"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Widget DNA
        self.dna_widget = DNAHelixWidget()
        self.dna_widget.setObjectName("dnaPanel")
        layout.addWidget(self.dna_widget)
        
        # Panneau de statut
        status_group = QGroupBox("📊 MONITORING BIOLOGIQUE")
        status_layout = QVBoxLayout()
        
        # Taux de mutation
        mutation_layout = QHBoxLayout()
        mutation_layout.addWidget(QLabel("Taux de mutation:"))
        self.mutation_rate_label = QLabel("0%")
        self.mutation_rate_label.setObjectName("mutationRate")
        mutation_layout.addWidget(self.mutation_rate_label)
        status_layout.addLayout(mutation_layout)
        
        # Stats
        stats_layout = QGridLayout()
        stats_layout.addWidget(QLabel("Taille originale:"), 0, 0)
        self.original_size_label = QLabel("-")
        stats_layout.addWidget(self.original_size_label, 0, 1)
        
        stats_layout.addWidget(QLabel("Taille protégée:"), 1, 0)
        self.protected_size_label = QLabel("-")
        stats_layout.addWidget(self.protected_size_label, 1, 1)
        
        stats_layout.addWidget(QLabel("Ratio:"), 2, 0)
        self.ratio_label = QLabel("-")
        stats_layout.addWidget(self.ratio_label, 2, 1)
        
        status_layout.addLayout(stats_layout)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Code C#
        code_group = QGroupBox("💻 SÉQUENCE C# GÉNÉRÉE")
        code_layout = QVBoxLayout()
        
        self.code_editor = QTextEdit()
        self.code_editor.setReadOnly(True)
        self.code_editor.setFont(QFont("Consolas", 9))
        code_layout.addWidget(self.code_editor)
        
        save_btn = QPushButton("💾 Sauvegarder la séquence")
        save_btn.clicked.connect(self.save_code)
        code_layout.addWidget(save_btn)
        
        code_group.setLayout(code_layout)
        layout.addWidget(code_group)
        
        return panel
        
    def toggle_expiration(self, state):
        """Active/désactive la date d'expiration"""
        self.expiration_date.setEnabled(state == Qt.Checked)
        
    def load_executable(self):
        """Charge un fichier exécutable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un exécutable",
            "",
            "Exécutables (*.exe);;Tous les fichiers (*)"
        )
        
        if file_path:
            self.current_exe_path = file_path
            self.file_label.setText(f"📄 {Path(file_path).name}")
            self.file_label.setToolTip(file_path)
            self.status_label.setText(f"Fichier chargé: {Path(file_path).name}")
            
            # Animation DNA
            self.dna_widget.set_mutation_points([random.randint(10, 90) for _ in range(5)])
            
    def start_mutation(self):
        """Démarre le processus de mutation"""
        if not self.current_exe_path:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord charger un exécutable!")
            return
            
        # Préparer la configuration
        config_dict = {
            'compression_enabled': self.compression_check.isChecked(),
            'compression_algo': self.compression_combo.currentText(),
            'compression_level': self.compression_level.value(),
            'compression_layers': self.compression_layers.value(),
            'encryption_enabled': self.encryption_check.isChecked(),
            'encryption_algo': self.encryption_combo.currentText(),
            'pbkdf2_iterations': self.pbkdf2_iterations.value(),
            'anti_debug': self.anti_debug.isChecked(),
            'anti_vm': self.anti_vm.isChecked(),
            'anti_sandbox': self.anti_vm.isChecked(),
            'execution_mode': self.execution_mode.currentText(),
            'integrity_check': self.integrity_check.isChecked(),
        }
        
        if self.expiration_check.isChecked():
            days = self.expiration_date.currentData()
            expiry = datetime.now() + timedelta(days=days)
            config_dict['expiration_date'] = expiry.strftime("%Y-%m-%d")
        else:
            config_dict['expiration_date'] = None
            
        # Démarrer le thread
        self.progress_bar.setVisible(True)
        self.mutate_btn.setEnabled(False)
        self.status_label.setText("Mutation en cours...")
        
        self.thread = ProtectionThread(self.current_exe_path, config_dict)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(self.status_label.setText)
        self.thread.finished_signal.connect(self.mutation_complete)
        self.thread.error.connect(self.mutation_error)
        self.thread.start()
        
    def mutation_complete(self, result):
        """Callback quand la mutation est terminée"""
        self.last_result = result
        self.mutate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Mettre à jour les stats
        payload = result['payload_data']
        self.original_size_label.setText(f"{payload['original_size']:,} octets")
        self.protected_size_label.setText(f"{payload['protected_size']:,} octets")
        self.ratio_label.setText(f"{payload['compression_ratio']:.1f}%")
        
        # Taux de mutation aléatoire pour l'effet visuel
        mutation_rate = random.uniform(85, 99)
        self.mutation_rate_label.setText(f"{mutation_rate:.1f}%")
        
        # Afficher le code
        self.code_editor.setPlainText(result['csharp_code'])
        
        # Points de mutation visuels
        self.dna_widget.set_mutation_points([random.randint(5, 95) for _ in range(8)])
        
        self.status_label.setText("✅ Mutation génétique complétée avec succès!")
        QMessageBox.information(self, "Succès", "La séquence protégée a été générée avec succès!")
        
    def mutation_error(self, error_msg):
        """Callback en cas d'erreur"""
        self.mutate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Erreur de mutation")
        QMessageBox.critical(self, "Erreur", f"Erreur lors de la mutation:\n{error_msg}")
        
    def save_code(self):
        """Sauvegarde le code C# généré"""
        if not self.last_result:
            QMessageBox.warning(self, "Attention", "Aucun code à sauvegarder!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le code C#",
            "ProtectedLoader.cs",
            "Fichiers C# (*.cs);;Tous les fichiers (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.last_result['csharp_code'])
                    
                # Sauvegarder aussi les métadonnées
                meta_path = file_path + ".meta.json"
                with open(meta_path, 'w') as f:
                    json.dump({
                        'original_size': self.last_result['payload_data']['original_size'],
                        'protected_size': self.last_result['payload_data']['protected_size'],
                        'compression_ratio': self.last_result['payload_data']['compression_ratio'],
                        'generated_at': datetime.now().isoformat(),
                    }, f, indent=2)
                    
                QMessageBox.information(self, "Succès", f"Code sauvegardé:\n{file_path}\n\nMétadonnées:\n{meta_path}")
                self.status_label.setText(f"Code sauvegardé: {Path(file_path).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")


# ============================================================
# POINT D'ENTRÉE
# ============================================================
if __name__ == '__main__':
    import math
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = CodeCartographerLab()
    window.show()
    
    sys.exit(app.exec_())

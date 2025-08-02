import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QInputDialog,
    QScrollArea,
    QMenuBar,
    QMenu,
)
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QAction
from PyQt6.QtCore import Qt, QSettings, QTimer
from updater import Updater


class DetalhePendenciaDialog(QDialog):
    def __init__(self, dados_pendencia, parent=None):
        super().__init__(parent)
        self.dados_pendencia = dados_pendencia
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Detalhes - {self.dados_pendencia['nome_tecnico']}")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Informações gerais
        info_group = QGroupBox("Informações da Pendência")
        info_layout = QVBoxLayout(info_group)

        info_layout.addWidget(
            QLabel(f"Técnico: {self.dados_pendencia['nome_tecnico']}")
        )
        info_layout.addWidget(QLabel(f"Data/Hora: {self.dados_pendencia['data_hora']}"))
        info_layout.addWidget(QLabel(f"Status: {self.dados_pendencia['status']}"))

        # Mostrar observações se existirem
        observacoes = self.dados_pendencia["dados"].get("observacoes", "").strip()
        if observacoes:
            obs_label = QLabel(f"Observações: {observacoes}")
            obs_label.setWordWrap(True)
            obs_label.setStyleSheet(
                "QLabel { background-color: #f8f9fa; padding: 8px; border-radius: 4px; border: 1px solid #e9ecef; }"
            )
            info_layout.addWidget(obs_label)

        layout.addWidget(info_group)

        # Campos preenchidos
        campos_group = QGroupBox("Campos Preenchidos")
        campos_layout = QVBoxLayout(campos_group)

        texto_campos = QTextEdit()
        texto_campos.setReadOnly(True)
        texto_campos.setMaximumHeight(150)

        campos_info = []
        dados = self.dados_pendencia["dados"]

        # Checkboxes
        if dados.get("check_comissao"):
            campos_info.append("✓ Comissão Técnico")
        if dados.get("check_ip_mac"):
            campos_info.append("✓ IP/MAC")
        if dados.get("check_instalacao"):
            campos_info.append("✓ Instalação")
        if dados.get("check_localizacao"):
            campos_info.append("✓ Localização")
        if dados.get("check_foto_gps"):
            campos_info.append("✓ Foto da Casa + GPS")
        if dados.get("check_acesso_remoto"):
            campos_info.append("✓ Acesso Remoto")

        # Outros campos
        if dados.get("combo_comodato"):
            campos_info.append(f"Comodato: {dados['combo_comodato']}")
        if dados.get("input_senha"):
            campos_info.append(f"Senha Router: {dados['input_senha']}")
        if dados.get("input_rx"):
            campos_info.append(f"Sinal RX: {dados['input_rx']}")
        if dados.get("input_tx"):
            campos_info.append(f"Sinal TX: {dados['input_tx']}")
        if dados.get("input_nome_arquivo"):
            campos_info.append(f"Nome Arquivo: {dados['input_nome_arquivo']}")
        if dados.get("input_link_gps"):
            campos_info.append(f"Link GPS: {dados['input_link_gps']}")

        texto_campos.setPlainText(
            "\n".join(campos_info) if campos_info else "Nenhum campo preenchido"
        )
        campos_layout.addWidget(texto_campos)

        layout.addWidget(campos_group)

        # Botões
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class ChecklistApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("ChecklistFibra", "WindowSettings")
        self.pendencias_file = "checklist_pendencias.json"
        self.pendencias = self.carregar_pendencias()
        self.carregando_tabela = False  # Flag para controlar eventos durante carregamento
        
        # Configuração do sistema de atualização
        self.current_version = "1.1"
        self.updater = Updater(
            current_version=self.current_version,
            version_url="https://raw.githubusercontent.com/DreamerJP/POS-assistencia/refs/heads/main/version.json"
        )
        
        self.initUI()
        self.load_settings()
        
        # Verificar atualizações na inicialização (após 2 segundos)
        QTimer.singleShot(2000, self.check_updates_on_startup)

    def carregar_pendencias(self):
        """Carrega as pendências do arquivo JSON"""
        try:
            if os.path.exists(self.pendencias_file):
                with open(self.pendencias_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar pendências: {e}")
        return []

    def salvar_pendencias(self):
        """Salva as pendências no arquivo JSON"""
        try:
            with open(self.pendencias_file, "w", encoding="utf-8") as f:
                json.dump(self.pendencias, f, ensure_ascii=False, indent=2)
            print(f"DEBUG: Pendências salvas com sucesso. Total: {len(self.pendencias)}")
        except Exception as e:
            self.mostrar_erro(f"Erro ao salvar pendências: {str(e)}")

    def load_settings(self):
        """Carrega as configurações salvas da janela"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def save_settings(self):
        """Salva as configurações da janela"""
        self.settings.setValue("geometry", self.saveGeometry())

    def initUI(self):
        self.setWindowTitle("Check-list Pós-Instalação - Fibra Óptica v" + self.current_version)
        # Tamanho inicial menor e mais apropriado
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(700, 500)

        # Set the window icon
        icon_path = "C:\\Users\\Sweet\\Desktop\\POS instalação CheckList\\ico.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Criar barra de menus
        self.create_menu_bar()

        # Estilo minimalista com paleta monocromática
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 6px;
                margin-top: 3px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                min-width: 80px;
                border: 1px solid #dee2e6;
                border-bottom: none;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #2c3e50;
                border-bottom: 2px solid #6c757d;
            }
            
            QGroupBox {
                font-weight: 600;
                font-size: 12px;
                color: #495057;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 4px 12px 4px 12px;
                color: #495057;
                background-color: white;
                font-weight: 700;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                margin-top: 5px;
            }
            
            QPushButton {
                border: none;
                color: white;
                padding: 6px 12px;
                text-align: center;
                font-size: 11px;
                font-weight: 600;
                border-radius: 4px;
                min-height: 25px;
                background-color: #6c757d;
            }
            
            QPushButton:hover {
                background-color: #5a6268;
            }
            
            QPushButton:pressed {
                background-color: #495057;
            }
            
            QLineEdit, QComboBox {
                padding: 6px 8px;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                font-size: 11px;
                background-color: white;
                color: #495057;
                min-height: 16px;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border-color: #6c757d;
                outline: none;
            }
            
            QTextEdit {
                padding: 8px;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                font-size: 11px;
                background-color: white;
                color: #495057;
            }
            
            QCheckBox {
                font-size: 11px;
                color: #495057;
                spacing: 6px;
                padding: 3px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 1px solid #6c757d;
                border-radius: 3px;
                background-color: #6c757d;
            }
            
            QLabel {
                font-size: 11px;
                color: #495057;
            }
            
            QTableWidget {
                gridline-color: #e9ecef;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #6c757d;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-size: 11px;
            }
            
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            
            QTableWidget QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: 600;
                font-size: 11px;
                color: #495057;
            }
        """
        )

        # Widget central com abas
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Criar abas
        self.tab_widget = QTabWidget()

        # Aba 1: Check-list Principal
        self.tab_checklist = self.criar_aba_checklist()
        self.tab_widget.addTab(self.tab_checklist, "📋 Check-list")

        # Aba 2: Gerenciar Pendências
        self.tab_pendencias = self.criar_aba_pendencias()
        self.tab_widget.addTab(self.tab_pendencias, "⏰ Pendências")

        main_layout.addWidget(self.tab_widget)

    def criar_aba_checklist(self):
        """Cria a aba principal do check-list com layout responsivo"""
        tab = QWidget()

        # Usar scroll area para permitir rolagem quando necessário
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)

        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Título principal mais compacto
        title_label = QLabel("Check-list Pós-Instalação Fibra Óptica")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(
            """
            QLabel {
                color: #2c3e50;
                background-color: #f8f9fa;
                padding: 12px;
                border-radius: 8px;
                border: 2px solid #6c757d;
                margin-bottom: 8px;
            }
        """
        )
        layout.addWidget(title_label)

        # Seção de Informações Gerais mais compacta
        info_group = QGroupBox("Informações Gerais")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(15, 20, 15, 15)

        # Nome do técnico
        info_layout.addWidget(QLabel("Técnico:"), 0, 0)
        self.input_nome_tecnico = QLineEdit()
        self.input_nome_tecnico.setPlaceholderText("Nome do técnico")
        info_layout.addWidget(self.input_nome_tecnico, 0, 1)

        # Observações mais compactas
        info_layout.addWidget(QLabel("Obs:"), 1, 0, Qt.AlignmentFlag.AlignTop)
        self.input_observacoes = QTextEdit()
        self.input_observacoes.setPlaceholderText("Observações, cliente, motivo...")
        self.input_observacoes.setMaximumHeight(60)
        self.input_observacoes.setAcceptRichText(False)
        info_layout.addWidget(self.input_observacoes, 1, 1)

        layout.addWidget(info_group)

        # Usar Splitter para dividir horizontalmente de forma responsiva
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)

        # Widget da esquerda
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(8)

        # Campos Padrão mais compactos
        self.group_campos = QGroupBox("Campos Padrão")
        campos_layout = QVBoxLayout(self.group_campos)
        campos_layout.setContentsMargins(15, 20, 15, 15)
        campos_layout.setSpacing(8)

        self.check_comissao = QCheckBox("1 - Comissão (120)")
        self.check_ip_mac = QCheckBox("4 - IP/MAC OK")
        self.check_instalacao = QCheckBox("6 - Instalação Padrão")
        self.check_localizacao = QCheckBox("7 - Localização OK")
        self.check_foto_gps = QCheckBox("8 - Foto + GPS")

        for checkbox in [
            self.check_comissao,
            self.check_ip_mac,
            self.check_instalacao,
            self.check_localizacao,
            self.check_foto_gps,
        ]:
            campos_layout.addWidget(checkbox)

        left_layout.addWidget(self.group_campos)

        # Comodato mais compacto
        self.group_comodato = QGroupBox("2 - Comodato")
        comodato_layout = QVBoxLayout(self.group_comodato)
        comodato_layout.setContentsMargins(15, 20, 15, 15)

        self.combo_comodato = QComboBox()
        self.combo_comodato.addItems(
            [
                "Selecione...",
                "ONT Zyxel",
                "ONU SUMEC + AX2",
                "ONU SUMEC + AX3",
                "ONU ZTE + AX2",
                "ONU ZTE + AX3",
                "ONT ZTE",
                "ONT TP-LINK",
            ]
        )
        comodato_layout.addWidget(self.combo_comodato)

        left_layout.addWidget(self.group_comodato)

        # Acesso Remoto compacto
        self.group_acesso = QGroupBox("3 - Acesso Remoto")
        acesso_layout = QVBoxLayout(self.group_acesso)
        acesso_layout.setContentsMargins(15, 20, 15, 15)
        acesso_layout.setSpacing(8)

        self.check_acesso_remoto = QCheckBox("Acesso OK")
        acesso_layout.addWidget(self.check_acesso_remoto)

        senha_layout = QHBoxLayout()
        senha_layout.addWidget(QLabel("Senha:"))
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha router")
        senha_layout.addWidget(self.input_senha)
        acesso_layout.addLayout(senha_layout)

        left_layout.addWidget(self.group_acesso)

        # Potência Fibra compacta
        self.group_potencia = QGroupBox("5 - Potência")
        potencia_layout = QGridLayout(self.group_potencia)
        potencia_layout.setContentsMargins(15, 20, 15, 15)
        potencia_layout.setSpacing(8)

        potencia_layout.addWidget(QLabel("RX:"), 0, 0)
        self.input_rx = QLineEdit()
        self.input_rx.setPlaceholderText("20.044")
        potencia_layout.addWidget(self.input_rx, 0, 1)

        potencia_layout.addWidget(QLabel("TX:"), 1, 0)
        self.input_tx = QLineEdit()
        self.input_tx.setPlaceholderText("24.611")
        potencia_layout.addWidget(self.input_tx, 1, 1)

        left_layout.addWidget(self.group_potencia)

        main_splitter.addWidget(left_widget)

        # Widget da direita
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)

        # GPS compacto
        self.group_gps = QGroupBox("GPS - Localização")
        gps_layout = QVBoxLayout(self.group_gps)
        gps_layout.setContentsMargins(15, 20, 15, 15)
        gps_layout.setSpacing(8)

        # Arquivo
        arquivo_layout = QHBoxLayout()
        label_arquivo = QLabel("Arquivo:")
        label_arquivo.setFixedWidth(50)  # Largura fixa para alinhar
        arquivo_layout.addWidget(label_arquivo)
        self.input_nome_arquivo = QLineEdit()
        self.input_nome_arquivo.setPlaceholderText("12345 - João Silva")
        arquivo_layout.addWidget(self.input_nome_arquivo)
        gps_layout.addLayout(arquivo_layout)

        # Link GPS
        link_layout = QHBoxLayout()
        label_link = QLabel("Link:")
        label_link.setFixedWidth(50)  # Mesma largura fixa para alinhar
        link_layout.addWidget(label_link)
        self.input_link_gps = QLineEdit()
        self.input_link_gps.setPlaceholderText("Link Google Maps")
        link_layout.addWidget(self.input_link_gps)
        gps_layout.addLayout(link_layout)

        # Botão GPS
        self.btn_gerar_gps = QPushButton("📍 Gerar GPS")
        self.btn_gerar_gps.clicked.connect(self.gerar_arquivo_gps)
        self.btn_gerar_gps.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                font-size: 12px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )
        gps_layout.addWidget(self.btn_gerar_gps)

        right_layout.addWidget(self.group_gps)

        # Resultado do Check-list mais compacto
        result_group = QGroupBox("Resultado")
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(15, 20, 15, 15)

        self.resultado_text = QTextEdit()
        self.resultado_text.setMinimumHeight(120)
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #f8f9fa;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                line-height: 1.3;
                border: 1px solid #e9ecef;
            }
        """
        )
        result_layout.addWidget(self.resultado_text)

        right_layout.addWidget(result_group)

        # Ações compactas
        actions_group = QGroupBox("Ações")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(15, 20, 15, 15)
        actions_layout.setSpacing(6)

        self.btn_salvar_pendencia = QPushButton("💾 Salvar Pendência")
        self.btn_salvar_pendencia.clicked.connect(self.salvar_como_pendencia)
        self.btn_salvar_pendencia.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        self.btn_gerar_relatorio = QPushButton("📋 Gerar Relatório")
        self.btn_gerar_relatorio.clicked.connect(self.gerar_relatorio)
        self.btn_gerar_relatorio.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        self.btn_limpar = QPushButton("🗑️ Limpar")
        self.btn_limpar.clicked.connect(self.limpar_campos)
        self.btn_limpar.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        actions_layout.addWidget(self.btn_salvar_pendencia)
        actions_layout.addWidget(self.btn_gerar_relatorio)
        actions_layout.addWidget(self.btn_limpar)

        right_layout.addWidget(actions_group)

        main_splitter.addWidget(right_widget)

        # Definir proporções do splitter (40% esquerda, 60% direita)
        main_splitter.setSizes([300, 450])

        layout.addWidget(main_splitter)

        # Layout principal do tab
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

        # Conectar eventos de validação
        self.conectar_eventos_validacao()
        self.validar_e_atualizar_bordas()

        return tab

    def atualizar_borda_campo(self, campo, preenchido):
        """Atualiza a cor da borda do campo baseado no status de preenchimento"""
        if preenchido:
            campo.setStyleSheet(
                f"""
                {campo.__class__.__name__} {{
                    padding: 6px 8px;
                    border: 2px solid #6c757d;
                    border-radius: 4px;
                    font-size: 11px;
                    background-color: white;
                    color: #495057;
                    min-height: 16px;
                }}
                {campo.__class__.__name__}:focus {{
                    border-color: #6c757d;
                    outline: none;
                }}
            """
            )
        else:
            campo.setStyleSheet(
                f"""
                {campo.__class__.__name__} {{
                    padding: 6px 8px;
                    border: 2px solid #dc3545;
                    border-radius: 4px;
                    font-size: 11px;
                    background-color: white;
                    color: #495057;
                    min-height: 16px;
                }}
                {campo.__class__.__name__}:focus {{
                    border-color: #dc3545;
                    outline: none;
                }}
            """
            )

    def atualizar_borda_groupbox(self, groupbox, preenchido):
        """Atualiza a cor da borda do groupbox baseado no status de preenchimento"""
        if preenchido:
            groupbox.setStyleSheet(
                f"""
                QGroupBox {{
                    font-weight: 600;
                    font-size: 12px;
                    color: #495057;
                    border: 2px solid #6c757d;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                    background-color: white;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #6c757d;
                    background-color: white;
                    font-weight: bold;
                }}
            """
            )
        else:
            groupbox.setStyleSheet(
                f"""
                QGroupBox {{
                    font-weight: 600;
                    font-size: 12px;
                    color: #495057;
                    border: 2px solid #dc3545;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                    background-color: white;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #dc3545;
                    background-color: white;
                    font-weight: bold;
                }}
            """
            )

    def validar_e_atualizar_bordas(self):
        """Valida todos os campos e atualiza suas bordas"""
        # Nome do técnico
        nome_preenchido = bool(self.input_nome_tecnico.text().strip())
        self.atualizar_borda_campo(self.input_nome_tecnico, nome_preenchido)

        # Checkboxes obrigatórios
        checkboxes_preenchidos = (
            self.check_comissao.isChecked()
            and self.check_ip_mac.isChecked()
            and self.check_instalacao.isChecked()
            and self.check_localizacao.isChecked()
            and self.check_foto_gps.isChecked()
        )
        self.atualizar_borda_groupbox(self.group_campos, checkboxes_preenchidos)

        # Comodato
        comodato_preenchido = self.combo_comodato.currentIndex() > 0
        self.atualizar_borda_campo(self.combo_comodato, comodato_preenchido)
        self.atualizar_borda_groupbox(self.group_comodato, comodato_preenchido)

        # Acesso remoto
        acesso_remoto_preenchido = self.check_acesso_remoto.isChecked() and bool(
            self.input_senha.text().strip()
        )
        self.atualizar_borda_campo(
            self.input_senha, bool(self.input_senha.text().strip())
        )
        self.atualizar_borda_groupbox(self.group_acesso, acesso_remoto_preenchido)

        # Potência
        potencia_preenchida = bool(self.input_rx.text().strip()) and bool(
            self.input_tx.text().strip()
        )
        self.atualizar_borda_campo(self.input_rx, bool(self.input_rx.text().strip()))
        self.atualizar_borda_campo(self.input_tx, bool(self.input_tx.text().strip()))
        self.atualizar_borda_groupbox(self.group_potencia, potencia_preenchida)

        # GPS (opcional - apenas visual)
        gps_preenchido = bool(self.input_nome_arquivo.text().strip()) and bool(
            self.input_link_gps.text().strip()
        )
        self.atualizar_borda_campo(
            self.input_nome_arquivo, bool(self.input_nome_arquivo.text().strip())
        )
        self.atualizar_borda_campo(
            self.input_link_gps, bool(self.input_link_gps.text().strip())
        )

    def conectar_eventos_validacao(self):
        """Conecta eventos para validação em tempo real"""
        # Nome do técnico
        self.input_nome_tecnico.textChanged.connect(self.validar_e_atualizar_bordas)

        # Checkboxes
        self.check_comissao.toggled.connect(self.validar_e_atualizar_bordas)
        self.check_ip_mac.toggled.connect(self.validar_e_atualizar_bordas)
        self.check_instalacao.toggled.connect(self.validar_e_atualizar_bordas)
        self.check_localizacao.toggled.connect(self.validar_e_atualizar_bordas)
        self.check_foto_gps.toggled.connect(self.validar_e_atualizar_bordas)
        self.check_acesso_remoto.toggled.connect(self.validar_e_atualizar_bordas)

        # Comodato
        self.combo_comodato.currentIndexChanged.connect(self.validar_e_atualizar_bordas)

        # Campos de texto
        self.input_senha.textChanged.connect(self.validar_e_atualizar_bordas)
        self.input_rx.textChanged.connect(self.validar_e_atualizar_bordas)
        self.input_tx.textChanged.connect(self.validar_e_atualizar_bordas)
        self.input_nome_arquivo.textChanged.connect(self.validar_e_atualizar_bordas)
        self.input_link_gps.textChanged.connect(self.validar_e_atualizar_bordas)

    def criar_aba_pendencias(self):
        """Cria a aba de gerenciamento de pendências"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Título compacto
        title_label = QLabel("Gerenciamento de Pendências")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(
            """
            QLabel {
                color: #2c3e50;
                background-color: #f8f9fa;
                padding: 12px;
                border-radius: 8px;
                border: 2px solid #6c757d;
                margin-bottom: 8px;
            }
        """
        )
        layout.addWidget(title_label)

        # Botões de ação mais compactos
        buttons_group = QGroupBox("Ações")
        buttons_layout = QHBoxLayout(buttons_group)
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(15, 20, 15, 15)

        self.btn_atualizar_pendencias = QPushButton("🔄 Atualizar")
        self.btn_atualizar_pendencias.clicked.connect(self.atualizar_lista_pendencias)
        self.btn_atualizar_pendencias.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        self.btn_carregar_pendencia = QPushButton("📂 Carregar")
        self.btn_carregar_pendencia.clicked.connect(self.carregar_pendencia_selecionada)
        self.btn_carregar_pendencia.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        self.btn_finalizar_pendencia = QPushButton("✅ Finalizar")
        self.btn_finalizar_pendencia.clicked.connect(
            self.finalizar_pendencia_selecionada
        )
        self.btn_finalizar_pendencia.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        self.btn_excluir_pendencia = QPushButton("🗑️ Excluir")
        self.btn_excluir_pendencia.clicked.connect(self.excluir_pendencia_selecionada)
        self.btn_excluir_pendencia.setStyleSheet(
            """
            QPushButton {
                background-color: #6c757d;
                font-size: 11px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """
        )

        buttons_layout.addWidget(self.btn_atualizar_pendencias)
        buttons_layout.addWidget(self.btn_carregar_pendencia)
        buttons_layout.addWidget(self.btn_finalizar_pendencia)
        buttons_layout.addWidget(self.btn_excluir_pendencia)
        buttons_layout.addStretch()

        layout.addWidget(buttons_group)

        # Tabela de pendências mais compacta
        self.tabela_pendencias = QTableWidget()
        self.tabela_pendencias.setColumnCount(6)
        self.tabela_pendencias.setHorizontalHeaderLabels(
            ["Técnico", "Observações", "Data/Hora", "Status", "Progresso", "Ações"]
        )

        # Configurar tabela para ser responsiva
        header = self.tabela_pendencias.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(5, 50)

        self.tabela_pendencias.setAlternatingRowColors(True)
        self.tabela_pendencias.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela_pendencias.verticalHeader().setDefaultSectionSize(45)
        # Permitir quebra de linha automática
        self.tabela_pendencias.setWordWrap(True)

        layout.addWidget(self.tabela_pendencias)

        # Conectar evento de edição
        self.tabela_pendencias.itemChanged.connect(self.salvar_edicao_pendencia)
        
        # Atualizar lista inicial
        self.atualizar_lista_pendencias()

        return tab

    def obter_dados_formulario(self):
        """Coleta todos os dados do formulário atual incluindo observações"""
        return {
            "nome_tecnico": self.input_nome_tecnico.text().strip(),
            "observacoes": self.input_observacoes.toPlainText().strip(),
            "check_comissao": self.check_comissao.isChecked(),
            "check_ip_mac": self.check_ip_mac.isChecked(),
            "check_instalacao": self.check_instalacao.isChecked(),
            "check_localizacao": self.check_localizacao.isChecked(),
            "check_foto_gps": self.check_foto_gps.isChecked(),
            "check_acesso_remoto": self.check_acesso_remoto.isChecked(),
            "combo_comodato": (
                self.combo_comodato.currentText()
                if self.combo_comodato.currentIndex() > 0
                else ""
            ),
            "input_senha": self.input_senha.text().strip(),
            "input_rx": self.input_rx.text().strip(),
            "input_tx": self.input_tx.text().strip(),
            "input_nome_arquivo": self.input_nome_arquivo.text().strip(),
            "input_link_gps": self.input_link_gps.text().strip(),
        }

    def preencher_formulario(self, dados):
        """Preenche o formulário com os dados fornecidos incluindo observações"""
        self.input_nome_tecnico.setText(dados.get("nome_tecnico", ""))
        self.input_observacoes.setPlainText(dados.get("observacoes", ""))
        self.check_comissao.setChecked(dados.get("check_comissao", False))
        self.check_ip_mac.setChecked(dados.get("check_ip_mac", False))
        self.check_instalacao.setChecked(dados.get("check_instalacao", False))
        self.check_localizacao.setChecked(dados.get("check_localizacao", False))
        self.check_foto_gps.setChecked(dados.get("check_foto_gps", False))
        self.check_acesso_remoto.setChecked(dados.get("check_acesso_remoto", False))

        # Combo box
        combo_text = dados.get("combo_comodato", "")
        if combo_text:
            index = self.combo_comodato.findText(combo_text)
            if index >= 0:
                self.combo_comodato.setCurrentIndex(index)
            else:
                self.combo_comodato.setCurrentIndex(0)
        else:
            self.combo_comodato.setCurrentIndex(0)

        self.input_senha.setText(dados.get("input_senha", ""))
        self.input_rx.setText(dados.get("input_rx", ""))
        self.input_tx.setText(dados.get("input_tx", ""))
        self.input_nome_arquivo.setText(dados.get("input_nome_arquivo", ""))
        self.input_link_gps.setText(dados.get("input_link_gps", ""))

        # Atualizar bordas após preencher
        self.validar_e_atualizar_bordas()

    def salvar_como_pendencia(self):
        """Salva o estado atual como pendência"""
        dados = self.obter_dados_formulario()

        if not dados["nome_tecnico"]:
            QMessageBox.warning(self, "Aviso", "Por favor, informe o nome do técnico!")
            return

        # Verificar se já existe uma pendência para este técnico com as mesmas observações
        for i, pendencia in enumerate(self.pendencias):
            if (
                pendencia["nome_tecnico"].lower() == dados["nome_tecnico"].lower()
                and pendencia["status"] == "Pendente"
                and pendencia["dados"].get("observacoes", "").lower()
                == dados["observacoes"].lower()
            ):

                resposta = QMessageBox.question(
                    self,
                    "Pendência Existente",
                    f"Já existe uma pendência similar para o técnico '{dados['nome_tecnico']}'.\n"
                    "Deseja atualizar os dados existentes?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )

                if resposta == QMessageBox.StandardButton.Yes:
                    # Atualizar pendência existente
                    self.pendencias[i]["dados"] = dados
                    self.pendencias[i]["data_hora"] = datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    )
                    self.salvar_pendencias()
                    self.atualizar_lista_pendencias()
                    QMessageBox.information(
                        self, "Sucesso", "Pendência atualizada com sucesso!"
                    )
                    return
                else:
                    return

        # Criar nova pendência
        nova_pendencia = {
            "nome_tecnico": dados["nome_tecnico"],
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "Pendente",
            "dados": dados,
        }

        self.pendencias.append(nova_pendencia)
        self.salvar_pendencias()
        self.atualizar_lista_pendencias()

        QMessageBox.information(
            self,
            "Sucesso",
            f"Pendência salva para o técnico '{dados['nome_tecnico']}'!",
        )

        # Limpar formulário após salvar
        self.limpar_campos()

    def atualizar_lista_pendencias(self):
        """Atualiza a tabela de pendências incluindo observações"""
        self.carregando_tabela = True  # Desabilitar eventos durante carregamento
        self.tabela_pendencias.setRowCount(len(self.pendencias))

        for i, pendencia in enumerate(self.pendencias):
            # Nome do técnico
            self.tabela_pendencias.setItem(
                i, 0, QTableWidgetItem(pendencia["nome_tecnico"])
            )

            # Observações - mostrar mais texto
            observacoes = pendencia["dados"].get("observacoes", "")
            if len(observacoes) > 80:
                observacoes_display = observacoes[:77] + "..."
            else:
                observacoes_display = observacoes

            obs_item = QTableWidgetItem(observacoes_display)
            obs_item.setToolTip(pendencia["dados"].get("observacoes", ""))
            # Permitir quebra de linha na célula
            obs_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.tabela_pendencias.setItem(i, 1, obs_item)

            # Data/Hora - NÃO editável
            data_item = QTableWidgetItem(pendencia["data_hora"])
            data_item.setFlags(data_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabela_pendencias.setItem(i, 2, data_item)

            # Status - NÃO editável
            status_item = QTableWidgetItem(pendencia["status"])
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if pendencia["status"] == "Finalizada":
                status_item.setBackground(QColor("white"))
            else:
                status_item.setBackground(QColor("white"))
            self.tabela_pendencias.setItem(i, 3, status_item)

            # Progresso (contar campos preenchidos) - NÃO editável
            dados = pendencia["dados"]
            total_campos = 11
            campos_preenchidos = 0

            if dados.get("check_comissao"):
                campos_preenchidos += 1
            if dados.get("check_ip_mac"):
                campos_preenchidos += 1
            if dados.get("check_instalacao"):
                campos_preenchidos += 1
            if dados.get("check_localizacao"):
                campos_preenchidos += 1
            if dados.get("check_foto_gps"):
                campos_preenchidos += 1
            if dados.get("check_acesso_remoto"):
                campos_preenchidos += 1
            if dados.get("input_senha"):
                campos_preenchidos += 1
            if dados.get("input_rx"):
                campos_preenchidos += 1
            if dados.get("input_tx"):
                campos_preenchidos += 1
            if dados.get("input_nome_arquivo"):
                campos_preenchidos += 1
            if dados.get("input_link_gps"):
                campos_preenchidos += 1

            progresso = f"{campos_preenchidos}/{total_campos}"
            progresso_item = QTableWidgetItem(progresso)
            progresso_item.setFlags(progresso_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabela_pendencias.setItem(i, 4, progresso_item)

            # Link clicável minimalista
            link_detalhes = QLabel("👁️")
            link_detalhes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            link_detalhes.setCursor(Qt.CursorShape.PointingHandCursor)
            link_detalhes.setToolTip("Ver detalhes")
            link_detalhes.setStyleSheet(
                """
                QLabel {
                    color: #6c757d;
                    font-size: 14px;
                    padding: 2px;
                    background-color: transparent;
                    border: none;
                }
                QLabel:hover {
                    color: #495057;
                    background-color: #f8f9fa;
                    border-radius: 3px;
                }
            """
            )
            
            # Conectar o clique do label
            link_detalhes.mousePressEvent = lambda event, idx=i: self.ver_detalhes_pendencia(idx)

            # Container simples
            container_widget = QWidget()
            container_layout = QHBoxLayout(container_widget)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.addWidget(link_detalhes)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabela_pendencias.setCellWidget(i, 5, container_widget)

        self.carregando_tabela = False  # Reabilitar eventos após carregamento

    def ver_detalhes_pendencia(self, index):
        """Mostra os detalhes de uma pendência"""
        if 0 <= index < len(self.pendencias):
            dialog = DetalhePendenciaDialog(self.pendencias[index], self)
            dialog.exec()

    def salvar_edicao_pendencia(self, item):
        """Salva as alterações feitas diretamente na tabela com confirmação"""
        if not item:
            return
            
        # Ignorar eventos durante carregamento da tabela
        if self.carregando_tabela:
            return
            
        row = item.row()
        col = item.column()
        
        print(f"DEBUG: itemChanged - Row: {row}, Col: {col}, Text: {item.text()}")
        
        if row >= len(self.pendencias):
            return
            
        # Verificar se é uma coluna editável
        if col == 0:  # Coluna Técnico
            print(f"DEBUG: Editando coluna Técnico - Row: {row}")
            novo_nome = item.text().strip()
            if novo_nome:
                resposta = self.mostrar_pergunta(
                    "Confirmar Alteração",
                    f"Deseja alterar o nome do técnico para '{novo_nome}'?"
                )
                if resposta == QMessageBox.StandardButton.Yes:
                    print(f"DEBUG: Salvando nome do técnico: {novo_nome}")
                    self.pendencias[row]["nome_tecnico"] = novo_nome
                    self.salvar_pendencias()
                    self.mostrar_sucesso(f"Nome do técnico atualizado para: {novo_nome}")
                else:
                    # Reverter a alteração
                    item.setText(self.pendencias[row]["nome_tecnico"])
                    
        elif col == 1:  # Coluna Observações
            print(f"DEBUG: Editando coluna Observações - Row: {row}")
            nova_obs = item.text().strip()
            resposta = self.mostrar_pergunta(
                "Confirmar Alteração",
                f"Deseja salvar as alterações nas observações?"
            )
            if resposta == QMessageBox.StandardButton.Yes:
                self.pendencias[row]["dados"]["observacoes"] = nova_obs
                self.salvar_pendencias()
                self.mostrar_sucesso("Observações atualizadas com sucesso!")
            else:
                # Reverter a alteração
                obs_original = self.pendencias[row]["dados"].get("observacoes", "")
                if len(obs_original) > 80:
                    obs_display = obs_original[:77] + "..."
                else:
                    obs_display = obs_original
                item.setText(obs_display)

    def carregar_pendencia_selecionada(self):
        """Carrega uma pendência selecionada no formulário"""
        row = self.tabela_pendencias.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Aviso", "Selecione uma pendência para carregar!"
            )
            return

        if row >= len(self.pendencias):
            QMessageBox.warning(self, "Erro", "Pendência inválida selecionada!")
            return

        pendencia = self.pendencias[row]

        # Verificar se há dados não salvos no formulário atual
        dados_atuais = self.obter_dados_formulario()
        tem_dados = any(
            [
                dados_atuais["nome_tecnico"],
                dados_atuais["observacoes"],
                dados_atuais["check_comissao"],
                dados_atuais["check_ip_mac"],
                dados_atuais["check_instalacao"],
                dados_atuais["check_localizacao"],
                dados_atuais["check_foto_gps"],
                dados_atuais["check_acesso_remoto"],
                dados_atuais["input_senha"],
                dados_atuais["input_rx"],
                dados_atuais["input_tx"],
                dados_atuais["input_nome_arquivo"],
                dados_atuais["input_link_gps"],
            ]
        )

        if tem_dados:
            resposta = QMessageBox.question(
                self,
                "Dados não salvos",
                "Há dados preenchidos no formulário atual que serão perdidos.\n"
                "Deseja continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if resposta == QMessageBox.StandardButton.No:
                return

        # Carregar dados da pendência
        self.preencher_formulario(pendencia["dados"])

        # Mudar para a aba do check-list
        self.tab_widget.setCurrentIndex(0)

        QMessageBox.information(
            self,
            "Sucesso",
            f"Pendência do técnico '{pendencia['nome_tecnico']}' carregada com sucesso!",
        )

    def excluir_pendencia_selecionada(self):
        """Exclui uma pendência selecionada"""
        row = self.tabela_pendencias.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Aviso", "Selecione uma pendência para excluir!"
            )
            return

        if row >= len(self.pendencias):
            QMessageBox.warning(self, "Erro", "Pendência inválida selecionada!")
            return

        pendencia = self.pendencias[row]

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a pendência do técnico '{pendencia['nome_tecnico']}'?\n"
            "Esta ação não pode ser desfeita!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            del self.pendencias[row]
            self.salvar_pendencias()
            self.atualizar_lista_pendencias()
            QMessageBox.information(self, "Sucesso", "Pendência excluída com sucesso!")

    def finalizar_pendencia_selecionada(self):
        """Marca uma pendência como finalizada"""
        row = self.tabela_pendencias.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Aviso", "Selecione uma pendência para finalizar!"
            )
            return

        if row >= len(self.pendencias):
            QMessageBox.warning(self, "Erro", "Pendência inválida selecionada!")
            return

        pendencia = self.pendencias[row]

        if pendencia["status"] == "Finalizada":
            QMessageBox.information(self, "Aviso", "Esta pendência já está finalizada!")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Finalização",
            f"Marcar a pendência do técnico '{pendencia['nome_tecnico']}' como finalizada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self.pendencias[row]["status"] = "Finalizada"
            self.pendencias[row]["data_finalizacao"] = datetime.now().strftime(
                "%d/%m/%Y %H:%M"
            )
            self.salvar_pendencias()
            self.atualizar_lista_pendencias()
            QMessageBox.information(
                self, "Sucesso", "Pendência marcada como finalizada!"
            )

    def gerar_arquivo_gps(self):
        nome_arquivo = self.input_nome_arquivo.text().strip()
        link_gps = self.input_link_gps.text().strip()

        if not nome_arquivo:
            self.mostrar_aviso("Por favor, preencha o nome do arquivo!")
            return

        if not link_gps:
            self.mostrar_aviso("Por favor, cole o link do GPS!")
            return

        # Gerar nome do arquivo
        nome_completo = f"Localização GPS {nome_arquivo}.txt"

        # Caminho da área de trabalho
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        caminho_arquivo = os.path.join(desktop, nome_completo)

        try:
            with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
                arquivo.write(link_gps)

            self.mostrar_sucesso(f"Arquivo GPS salvo com sucesso!\n{nome_completo}")

        except Exception as e:
            self.mostrar_erro(f"Erro ao salvar arquivo GPS:\n{str(e)}")

    def mostrar_aviso(self, mensagem):
        """Exibe uma mensagem de aviso com estilo minimalista"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Aviso")
        msg.setText(mensagem)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Estilo minimalista monocromático
        msg.setStyleSheet(
            """
            QMessageBox {
                background-color: #ffffff;
                border: 1px solid #6c757d;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 10px;
            }
            QMessageBox QLabel {
                color: #495057;
                background-color: transparent;
                padding: 15px;
                font-size: 12px;
                border: none;
            }
            QMessageBox QPushButton {
                background-color: #6c757d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: 600;
                min-width: 80px;
                margin: 5px;
            }
            QMessageBox QPushButton:hover {
                background-color: #5a6268;
            }
            QMessageBox QPushButton:pressed {
                background-color: #495057;
            }
        """
        )

        msg.exec()

    def mostrar_sucesso(self, mensagem):
        """Exibe uma mensagem de sucesso com estilo minimalista"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Sucesso")
        msg.setText(mensagem)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Estilo minimalista monocromático
        msg.setStyleSheet(
            """
            QMessageBox {
                background-color: #ffffff;
                border: 1px solid #6c757d;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 10px;
            }
            QMessageBox QLabel {
                color: #495057;
                background-color: transparent;
                padding: 15px;
                font-size: 12px;
                border: none;
            }
            QMessageBox QPushButton {
                background-color: #6c757d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: 600;
                min-width: 80px;
                margin: 5px;
            }
            QMessageBox QPushButton:hover {
                background-color: #5a6268;
            }
            QMessageBox QPushButton:pressed {
                background-color: #495057;
            }
        """
        )

        msg.exec()

    def mostrar_erro(self, mensagem):
        """Exibe uma mensagem de erro com estilo minimalista"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Erro")
        msg.setText(mensagem)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Estilo minimalista monocromático
        msg.setStyleSheet(
            """
            QMessageBox {
                background-color: #ffffff;
                border: 1px solid #6c757d;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 10px;
            }
            QMessageBox QLabel {
                color: #495057;
                background-color: transparent;
                padding: 15px;
                font-size: 12px;
                border: none;
            }
            QMessageBox QPushButton {
                background-color: #6c757d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: 600;
                min-width: 80px;
                margin: 5px;
            }
            QMessageBox QPushButton:hover {
                background-color: #5a6268;
            }
            QMessageBox QPushButton:pressed {
                background-color: #495057;
            }
        """
        )

        msg.exec()

    def mostrar_pergunta(
        self,
        titulo,
        mensagem,
        botoes=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    ):
        """Exibe uma mensagem de pergunta com estilo minimalista"""
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(mensagem)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(botoes)

        # Estilo minimalista monocromático
        msg.setStyleSheet(
            """
            QMessageBox {
                background-color: #ffffff;
                border: 1px solid #6c757d;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 10px;
            }
            QMessageBox QLabel {
                color: #495057;
                background-color: transparent;
                padding: 15px;
                font-size: 12px;
                border: none;
            }
            QMessageBox QPushButton {
                background-color: #6c757d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: 600;
                min-width: 80px;
                margin: 5px;
            }
            QMessageBox QPushButton:hover {
                background-color: #5a6268;
            }
            QMessageBox QPushButton:pressed {
                background-color: #495057;
            }
        """
        )

        return msg.exec()

    def gerar_relatorio(self):
        # Verificar se o nome do técnico está preenchido
        if not self.input_nome_tecnico.text().strip():
            self.mostrar_aviso("Por favor, informe o nome do técnico!")
            return

        # Verificar se todos os campos obrigatórios estão preenchidos
        campos_vazios = []

        # Verificar checkboxes obrigatórios
        if not self.check_comissao.isChecked():
            campos_vazios.append("1 - Comissão Técnico")
        if not self.check_ip_mac.isChecked():
            campos_vazios.append("4 - IP/MAC")
        if not self.check_instalacao.isChecked():
            campos_vazios.append("6 - Instalação")
        if not self.check_localizacao.isChecked():
            campos_vazios.append("7 - Localização")
        if not self.check_foto_gps.isChecked():
            campos_vazios.append("8 - Foto da Casa + GPS")

        # Verificar comodato
        if self.combo_comodato.currentIndex() <= 0:
            campos_vazios.append("2 - Comodato Cliente")

        # Verificar acesso remoto
        if not self.check_acesso_remoto.isChecked():
            campos_vazios.append("3 - Acesso Remoto (checkbox)")

        # Verificar senha
        if not self.input_senha.text().strip():
            campos_vazios.append("3 - Senha Router")

        # Verificar potências
        if not self.input_rx.text().strip():
            campos_vazios.append("5 - Sinal RX")
        if not self.input_tx.text().strip():
            campos_vazios.append("5 - Sinal TX")

        # Se houver campos vazios, mostrar aviso
        if campos_vazios:
            mensagem = "Os seguintes campos são obrigatórios:\n\n" + "\n".join(
                f"• {campo}" for campo in campos_vazios
            )
            self.mostrar_aviso(mensagem)
            return

        # Gerar relatório apenas se todos os campos estiverem preenchidos
        resultado = []

        # 1 - Comissão Técnico
        resultado.append("1-COMISSÃO TÉCNICO = 120 INSTALAÇÃO FIBRA PADRÃO")

        # 2 - Comodato Cliente
        resultado.append(f"2-COMODATO CLIENTE = {self.combo_comodato.currentText()}")

        # 3 - Acesso Remoto
        senha = self.input_senha.text().strip()
        resultado.append(f"3-ACESSO REMOTO = OK / SENHA ROUTER = {senha}")

        # 4 - IP/MAC
        resultado.append("4-IP/MAC = OK")

        # 5 - Potência Fibra
        rx = self.input_rx.text().strip()
        tx = self.input_tx.text().strip()

        rx_formatado = f"-{rx}" if not rx.startswith("-") else rx
        tx_formatado = f"-{tx}" if not tx.startswith("-") else tx
        resultado.append(
            f"5-POTENCIA FIBRA = Sinal Rx: {rx_formatado} / Sinal Tx: {tx_formatado}"
        )

        # 6 - Instalação
        resultado.append("6-INSTALAÇÃO = NO PADRÃO")

        # 7 - Localização
        resultado.append("7-LOCALIZAÇÃO = OK ATUALIZADO")

        # 8 - Foto da Casa + GPS
        resultado.append("8-FOTO DA CASA + GPS = Arquivado")

        # Exibir resultado
        texto_final = "\n".join(resultado)
        self.resultado_text.setPlainText(texto_final)

        # Remover pendência se existir para este técnico com as mesmas observações
        nome_tecnico = self.input_nome_tecnico.text().strip()
        obs_atuais = self.input_observacoes.toPlainText().strip()

        for i, pendencia in enumerate(self.pendencias):
            if (
                pendencia["nome_tecnico"].lower() == nome_tecnico.lower()
                and pendencia["status"] == "Pendente"
                and pendencia["dados"].get("observacoes", "").lower()
                == obs_atuais.lower()
            ):

                resposta = self.mostrar_pergunta(
                    "Pendência Encontrada",
                    f"Foi encontrada uma pendência para o técnico '{nome_tecnico}'.\n"
                    "Deseja removê-la da lista de pendências?",
                )

                if resposta == QMessageBox.StandardButton.Yes:
                    del self.pendencias[i]
                    self.salvar_pendencias()
                    self.atualizar_lista_pendencias()
                break

        self.mostrar_sucesso("Relatório gerado com sucesso!")

    def limpar_campos(self):
        # Desmarcar checkboxes
        for checkbox in [
            self.check_comissao,
            self.check_ip_mac,
            self.check_instalacao,
            self.check_localizacao,
            self.check_foto_gps,
            self.check_acesso_remoto,
        ]:
            checkbox.setChecked(False)

        # Resetar combo para o primeiro item (vazio)
        self.combo_comodato.setCurrentIndex(0)

        # Limpar campos de texto
        for field in [
            self.input_nome_tecnico,
            self.input_senha,
            self.input_rx,
            self.input_tx,
            self.input_nome_arquivo,
            self.input_link_gps,
        ]:
            field.clear()

        # Limpar observações
        self.input_observacoes.clear()

        # Limpar resultado
        self.resultado_text.clear()

        # Atualizar bordas após limpar
        self.validar_e_atualizar_bordas()

        self.mostrar_sucesso("Todos os campos foram limpos!")

    def salvar_como_pendencia(self):
        """Salva o estado atual como pendência"""
        dados = self.obter_dados_formulario()

        if not dados["nome_tecnico"]:
            self.mostrar_aviso("Por favor, informe o nome do técnico!")
            return

        # Verificar se já existe uma pendência para este técnico com as mesmas observações
        for i, pendencia in enumerate(self.pendencias):
            if (
                pendencia["nome_tecnico"].lower() == dados["nome_tecnico"].lower()
                and pendencia["status"] == "Pendente"
                and pendencia["dados"].get("observacoes", "").lower()
                == dados["observacoes"].lower()
            ):

                resposta = self.mostrar_pergunta(
                    "Pendência Existente",
                    f"Já existe uma pendência similar para o técnico '{dados['nome_tecnico']}'.\n"
                    "Deseja atualizar os dados existentes?",
                )

                if resposta == QMessageBox.StandardButton.Yes:
                    # Atualizar pendência existente
                    self.pendencias[i]["dados"] = dados
                    self.pendencias[i]["data_hora"] = datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    )
                    self.salvar_pendencias()
                    self.atualizar_lista_pendencias()
                    self.mostrar_sucesso("Pendência atualizada com sucesso!")
                    return
                else:
                    return

        # Criar nova pendência
        nova_pendencia = {
            "nome_tecnico": dados["nome_tecnico"],
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "Pendente",
            "dados": dados,
        }

        self.pendencias.append(nova_pendencia)
        self.salvar_pendencias()
        self.atualizar_lista_pendencias()

        self.mostrar_sucesso(
            f"Pendência salva para o técnico '{dados['nome_tecnico']}'!"
        )

        # Limpar formulário após salvar
        self.limpar_campos()

    def carregar_pendencia_selecionada(self):
        """Carrega uma pendência selecionada no formulário"""
        row = self.tabela_pendencias.currentRow()
        if row < 0:
            self.mostrar_aviso("Selecione uma pendência para carregar!")
            return

        if row >= len(self.pendencias):
            self.mostrar_erro("Pendência inválida selecionada!")
            return

        pendencia = self.pendencias[row]

        # Verificar se há dados não salvos no formulário atual
        dados_atuais = self.obter_dados_formulario()
        tem_dados = any(
            [
                dados_atuais["nome_tecnico"],
                dados_atuais["observacoes"],
                dados_atuais["check_comissao"],
                dados_atuais["check_ip_mac"],
                dados_atuais["check_instalacao"],
                dados_atuais["check_localizacao"],
                dados_atuais["check_foto_gps"],
                dados_atuais["check_acesso_remoto"],
                dados_atuais["input_senha"],
                dados_atuais["input_rx"],
                dados_atuais["input_tx"],
                dados_atuais["input_nome_arquivo"],
                dados_atuais["input_link_gps"],
            ]
        )

        if tem_dados:
            resposta = self.mostrar_pergunta(
                "Dados não salvos",
                "Há dados preenchidos no formulário atual que serão perdidos.\n"
                "Deseja continuar?",
            )

            if resposta == QMessageBox.StandardButton.No:
                return

        # Carregar dados da pendência
        self.preencher_formulario(pendencia["dados"])

        # Mudar para a aba do check-list
        self.tab_widget.setCurrentIndex(0)

        self.mostrar_sucesso(
            f"Pendência do técnico '{pendencia['nome_tecnico']}' carregada com sucesso!"
        )

    def excluir_pendencia_selecionada(self):
        """Exclui uma pendência selecionada"""
        row = self.tabela_pendencias.currentRow()
        if row < 0:
            self.mostrar_aviso("Selecione uma pendência para excluir!")
            return

        if row >= len(self.pendencias):
            self.mostrar_erro("Pendência inválida selecionada!")
            return

        pendencia = self.pendencias[row]

        resposta = self.mostrar_pergunta(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a pendência do técnico '{pendencia['nome_tecnico']}'?\n"
            "Esta ação não pode ser desfeita!",
        )

        if resposta == QMessageBox.StandardButton.Yes:
            del self.pendencias[row]
            self.salvar_pendencias()
            self.atualizar_lista_pendencias()
            self.mostrar_sucesso("Pendência excluída com sucesso!")

    def finalizar_pendencia_selecionada(self):
        """Marca uma pendência como finalizada"""
        row = self.tabela_pendencias.currentRow()
        if row < 0:
            self.mostrar_aviso("Selecione uma pendência para finalizar!")
            return

        if row >= len(self.pendencias):
            self.mostrar_erro("Pendência inválida selecionada!")
            return

        pendencia = self.pendencias[row]

        if pendencia["status"] == "Finalizada":
            self.mostrar_aviso("Esta pendência já está finalizada!")
            return

        resposta = self.mostrar_pergunta(
            "Confirmar Finalização",
            f"Marcar a pendência do técnico '{pendencia['nome_tecnico']}' como finalizada?",
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self.pendencias[row]["status"] = "Finalizada"
            self.pendencias[row]["data_finalizacao"] = datetime.now().strftime(
                "%d/%m/%Y %H:%M"
            )
            self.salvar_pendencias()
            self.atualizar_lista_pendencias()
            self.mostrar_sucesso("Pendência marcada como finalizada!")

    def create_menu_bar(self):
        """Cria a barra de menus com opção de atualização"""
        menubar = self.menuBar()
        
        # Menu Ajuda
        help_menu = menubar.addMenu("Ajuda")
        
        # Ação para verificar atualizações
        check_update_action = QAction("Verificar Atualizações", self)
        check_update_action.setShortcut("Ctrl+U")
        check_update_action.setStatusTip("Verificar se há atualizações disponíveis")
        check_update_action.triggered.connect(self.manual_update_check)
        help_menu.addAction(check_update_action)
        
        # Separador
        help_menu.addSeparator()
        
        # Ação para informações sobre
        about_action = QAction("Sobre", self)
        about_action.setStatusTip("Informações sobre o aplicativo")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def check_updates_on_startup(self):
        """Verifica atualizações automaticamente na inicialização"""
        try:
            version_info = self.updater.check_for_updates()
            if version_info:
                self.prompt_update(version_info)
        except Exception as e:
            print(f"Erro na verificação automática: {e}")

    def manual_update_check(self):
        """Verificação manual de atualizações (para menu)"""
        try:
            self.mostrar_sucesso("Verificando atualizações...")
            version_info = self.updater.check_for_updates()
            if version_info:
                self.prompt_update(version_info)
            else:
                self.mostrar_sucesso("Você já possui a versão mais recente!")
        except Exception as e:
            self.mostrar_erro(f"Erro ao verificar atualizações: {e}")

    def prompt_update(self, version_info):
        """Pergunta ao usuário se deseja atualizar"""
        # Formatar changelog
        changelog_text = ""
        if "changelog" in version_info:
            changelog = version_info["changelog"]
            if isinstance(changelog, dict):
                # Se changelog é um dicionário com versões
                for version, changes in changelog.items():
                    if version == version_info["version"]:
                        changelog_text = "\n".join([f"• {change}" for change in changes])
                        break
            else:
                # Se changelog é uma string simples
                changelog_text = changelog
        
        message = f"""Nova versão disponível!

Versão atual: {self.current_version}
Nova versão: {version_info['version']}

Changelog:
{changelog_text}

Deseja atualizar agora?"""
        
        resposta = self.mostrar_pergunta(
            "Atualização Disponível",
            message
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            self.updater.download_and_install(version_info["download_url"])

    def show_about(self):
        """Mostra informações sobre o aplicativo"""
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices
        
        # Criar diálogo personalizado
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("Sobre")
        about_dialog.setModal(True)
        about_dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(about_dialog)
        
        # Título
        title_label = QLabel("Check-list Pós-Instalação - Fibra Óptica")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)
        
        # Versão
        version_label = QLabel(f"Versão: {self.current_version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #495057; margin: 5px;")
        layout.addWidget(version_label)
        
        # Descrição
        desc_label = QLabel("Desenvolvido para facilitar o processo de\npós-instalação de fibra óptica.")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #495057; margin: 10px;")
        layout.addWidget(desc_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #dee2e6; margin: 10px;")
        layout.addWidget(separator)
        
        # Desenvolvedor
        dev_label = QLabel("Desenvolvedor: DreamerJP")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_label.setStyleSheet("color: #495057; margin: 5px;")
        layout.addWidget(dev_label)
        
        # Link GitHub (clicável)
        github_label = QLabel('<a href="https://github.com/DreamerJP" style="color: #007bff; text-decoration: none;">GitHub: https://github.com/DreamerJP</a>')
        github_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_label.setOpenExternalLinks(True)
        github_label.setStyleSheet("margin: 5px;")
        github_label.linkActivated.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
        layout.addWidget(github_label)
        
        # Copyright
        copyright_label = QLabel("© 2025 - Sistema de Atualização Automática")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: #6c757d; margin: 10px; font-size: 10px;")
        layout.addWidget(copyright_label)
        
        # Botão OK
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(about_dialog.accept)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        about_dialog.exec()

    def closeEvent(self, event):
        """Salva as configurações quando a janela é fechada"""
        # Verificar se há dados não salvos
        dados_atuais = self.obter_dados_formulario()
        tem_dados = any(
            [
                dados_atuais["nome_tecnico"],
                dados_atuais["observacoes"],
                dados_atuais["check_comissao"],
                dados_atuais["check_ip_mac"],
                dados_atuais["check_instalacao"],
                dados_atuais["check_localizacao"],
                dados_atuais["check_foto_gps"],
                dados_atuais["check_acesso_remoto"],
                dados_atuais["input_senha"],
                dados_atuais["input_rx"],
                dados_atuais["input_tx"],
                dados_atuais["input_nome_arquivo"],
                dados_atuais["input_link_gps"],
            ]
        )

        if tem_dados:
            resposta = self.mostrar_pergunta(
                "Dados não salvos",
                "Há dados preenchidos que não foram salvos como pendência.\n"
                "Deseja salvar como pendência antes de sair?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )

            if resposta == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif resposta == QMessageBox.StandardButton.Yes:
                if dados_atuais["nome_tecnico"]:
                    self.salvar_como_pendencia()
                else:
                    self.mostrar_aviso(
                        "Nome do técnico é obrigatório para salvar pendência!"
                    )
                    event.ignore()
                    return

        self.save_settings()
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Configurar fonte padrão menor para melhor aproveitamento
    font = QFont("Arial", 8)
    app.setFont(font)

    window = ChecklistApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

import re
import os
import sys
import sqlite3
import pandas as pd
import win32print
import logging
from datetime import datetime
import locale
from platformdirs import user_desktop_path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QDialog, QMessageBox,
    QCheckBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QFont, QIcon, QPixmap, QBrush
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtPrintSupport import QPrinter

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

# Cores e fontes (mantidas exatamente como você fez)
COR_GRADIENTE_INICIO = "#a8dcab"
COR_GRADIENTE_FIM = "#e0e0e0"
COR_BOTAO = "#658165"
COR_BOTAO_CARREGAR = "#658165"
COR_DESTAQUE_HOVER = "#658165"
COR_TEXTO_BOTAO = "#FFFFFF"
COR_TITULO = "#000000"
COR_RODAPE = "#666666"
FONT_TITULO = "Open Sans"

# Força o Python a usar português brasileiro para os meses
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'portuguese_brazil.1252')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR')
        except:
            pass

class GeradorDeclaracao(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Declaração do Bolsa Família")
        self.setFixedSize(1000, 600)

        # === ESTILO 100% ORIGINAL (não alterado) ===
        self.setStyleSheet(f"""
        /* ====================== BOTÕES ====================== */
        QPushButton {{
            background-color: {COR_BOTAO};
            color: {COR_TEXTO_BOTAO};
            font-weight: bold;
            padding: 12px 20px;
            border-radius: 8px;
            border: none ;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }}

        QPushButton#btn_montar {{
            background-color: {COR_BOTAO_CARREGAR};
            font-size: 14px;
        }}

        /* ====================== TEXTOS E LABELS ====================== */
        QLabel {{
            color: {COR_TITULO};
            font-weight: bold;
        }}

        QLabel#rodape_label {{
            color: {COR_RODAPE};
            font-weight: normal;
            font-size: 10px;
        }}

        /* ====================== CAMPOS DE ENTRADA E COMBOBOX ====================== */
        QLineEdit,
        QComboBox {{
            padding: 2px 14px;
            border: 2px solid #658165;
            border-radius: 10px;
            background-color: white;
            color: {COR_TITULO};
            font-weight: bold;
            font-size: 11px;
        }}

        /* ====================== ESTILO AVANÇADO DO QComboBox (setinha linda) ====================== */
        QComboBox {{
            padding-right: 50px;                     /* espaço para a setinha */
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 30px;
            border-left: 2px solid #658165;
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
            background-color: #658165;
        }}

        QComboBox::down-arrow {{
            width: 0;
            heigh: 0;
            border-left: 7px solid #658165;
            border-right: 7px solid #658165;
            border-top: 12px solid white;
            margin-top: 2px;
        }}

        QComboBox::down-arrow:on {{
            border-top: none;
            border-bottom: 12px solid white;
        }}

        QComboBox QAbstractItemView {{
            border: 2px solid #658165;
            background-color: white;
            selection-background-color: #86b089;
            selection-color: black;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            outline: none;
            padding: 8px;
        }}
    """)

        self.csv_files = []
        self.anos = []
        self.alunos_por_ano = {}
        self.dados_aluno = None

        BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.modelo_html = os.path.join(BASE_DIR, "modelo_bolsafamilia.html")
        self.modelo_frequencia_html = os.path.join(BASE_DIR, "modelo_bolsafamilia_frequencia.html")
        caminho_icone = os.path.join(BASE_DIR, "icone_bolsafamilia.ico")
        self.background_path = os.path.join(BASE_DIR, "background.png")
        self.caminho_salvamento = str(user_desktop_path())
        self.CAMPOS_OBRIGATORIOS = ["NOME COMPLETO", "DATA DE NASCIMENTO", "NATURALIDADE", "NOME DA MÃE", "NIS DO ALUNO", "GÊNERO"]
        self.db_path = os.path.join(BASE_DIR, "alunos_2025.db")  # ← seu banco se chama alunos.db

        self.carregar_do_banco()
        self.criar_interface()

        if self.anos:
            self.atualizar_alunos()

        if os.path.exists(caminho_icone):
            self.setWindowIcon(QIcon(caminho_icone))

        if not os.path.exists(self.modelo_html):
            QMessageBox.critical(self, "Erro", f"Arquivo não encontrado:\n{self.modelo_html}\n\nCrie o arquivo 'modelo_bolsafamilia.html' na mesma pasta!")

    # === SEUS MÉTODOS ORIGINAIS (sem alteração) ===
    def extrair_ano_turma(self, arquivo):
        match = re.match(r"(\d+)ºANO ([A-D])\.csv", arquivo)
        return match.group(1), match.group(2) if match else (None, None)

    def encontrar_coluna_nis(self, colunas):
        for col in colunas:
            if "NIS" in col.upper():
                return col
        return None

    def padronizar_texto(self, texto, case='upper'):
        if pd.isna(texto) or not texto or str(texto).strip().upper() in ["", "NÃO TEM NIS"]:
            return ""
        return str(texto).strip().upper() if case == 'upper' else str(texto).strip().lower()

    def carregar_do_banco(self):
        """Carrega alunos do banco SQLite (compatível com seu banco real 100%)"""
        
        if not os.path.exists(self.db_path):
            QMessageBox.critical(self, "Banco não encontrado", 
                f"Arquivo não encontrado:\n{self.db_path}")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT 
                    "NOME COMPLETO", "DATA DE NASCIMENTO", NATURALIDADE,
                    "NOME DA MÃE", "NOME DO PAI", "NIS DO ALUNO", GÊNERO,
                    ANO, TURMA, TRANSFERENCIA
                FROM "dados_dos_aluno"
                WHERE TRANSFERENCIA IS NULL 
                   OR TRANSFERENCIA = '' 
                   OR TRANSFERENCIA = '-'
                ORDER BY ANO, "NOME COMPLETO"
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                QMessageBox.information(self, "Atenção", "Nenhum aluno ativo encontrado.")
                return

            # Trata ANO como texto (remove º e espaços)
            df["ANO"] = df["ANO"].astype(str).str.strip().str.replace("º", "").str.replace("ANO", "", case=False)
            df["ANO"] = pd.to_numeric(df["ANO"], errors='coerce')  # converte pra número, ignora lixo
            df = df.dropna(subset=["ANO"])  # remove linhas inválidas
            df["ANO"] = df["ANO"].astype(int)

            # Padroniza texto
            texto_cols = ["NOME COMPLETO", "DATA DE NASCIMENTO", "NATURALIDADE", 
                         "NOME DA MÃE", "NOME DO PAI", "NIS DO ALUNO", "GÊNERO", "TURMA"]
            for col in texto_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.upper().replace({"NAN": "", "-": ""})

            # Monta nome dos pais
            df["NOME DOS PAIS"] = df["NOME DA MÃE"]
            mask_pai = df["NOME DO PAI"].notna() & (df["NOME DO PAI"].str.strip() != "") & (df["NOME DO PAI"].str.strip() != "-")
            df.loc[mask_pai, "NOME DOS PAIS"] += " E DE " + df.loc[mask_pai, "NOME DO PAI"]

            # Trata NIS
            df["NIS DO ALUNO"] = df["NIS DO ALUNO"].fillna("-")
            df["NIS DO ALUNO"] = df["NIS DO ALUNO"].replace({"": "-", "NAN": "-"})

            # Organiza por ano
            self.anos.clear()
            self.alunos_por_ano.clear()

            for ano in sorted(df["ANO"].unique()):
                ano_str = f"{ano}º ANO"
                self.anos.append(ano_str)
                dados_ano = df[df["ANO"] == ano]
                self.alunos_por_ano[ano_str] = [
                    (row["NOME COMPLETO"], row.to_dict())
                    for _, row in dados_ano.iterrows()
                    if pd.notna(row["NOME COMPLETO"]) and row["NOME COMPLETO"].strip()
                ] 

            log.info(f"Carregados {len(df)} alunos com sucesso!")

        except Exception as e:
            QMessageBox.critical(self, "Erro no banco", f"Falha ao carregar:\n{e}")
            log.error(f"Erro: {e}")

    def criar_interface(self):
        central = QWidget()
        self.setCentralWidget(central)

        # Widget com fundo (mantém como estava, com QPalette ou stylesheet)
        background_widget = QWidget(central)
        background_widget.setGeometry(0, 0, 1000, 600)  # cobre toda a janela

        if os.path.exists(self.background_path):
            palette = background_widget.palette()
            pixmap = QPixmap(self.background_path).scaled(1000, 600, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            palette.setBrush(background_widget.backgroundRole(), QBrush(pixmap))
            background_widget.setPalette(palette)
            background_widget.setAutoFillBackground(True)
        else:
            background_widget.setStyleSheet("background-color: #a8dcab;")  # fallback

        # Agora posiciona os elementos FILHOS do background_widget (ou do central)
        # Use as coordenadas X, Y (topo-esquerda), largura, altura em pixels

        # Combo Aluno
        self.aluno_dropdown = QComboBox(background_widget)
        self.aluno_dropdown.setFixedSize(295, 31)
        self.aluno_dropdown.setGeometry(90, 320, 450, 45)
        self.aluno_dropdown.setStyleSheet("background: white; border: 2px solid #658165;")
        self.aluno_dropdown.setEnabled(False)

        # Combo Ano
        self.ano_dropdown = QComboBox(background_widget)
        self.ano_dropdown.addItems(sorted(self.anos))
        self.ano_dropdown.setFixedSize(173, 31)
        self.ano_dropdown.setGeometry(90, 360, 250, 45)
        self.ano_dropdown.setStyleSheet("background: white; border: 2px solid #658165;")
        self.ano_dropdown.currentIndexChanged.connect(self.atualizar_alunos)

        # Botão Montar Documento
        btn = QPushButton("MONTAR DOCUMENTO", background_widget)
        btn.setFont(QFont(FONT_TITULO, 11, QFont.Bold))
        btn.setFixedSize(270, 50)
        btn.setGeometry(90, 410, 320, 35)   # ← centralizado embaixo, ajuste Y pra onde fica na arte
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #658165;
                color: white;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COR_DESTAQUE_HOVER};
            }}
        """)
        btn.clicked.connect(self.abrir_janela_edicao)

        # Rodapé (se não estiver na imagem)
        rodape = QLabel("@Elaborado pela Secretaria Escolar", background_widget)
        rodape.setObjectName("rodape_label")
        rodape.setGeometry(-380, 560, 1000, 40)  # embaixo da tela
        rodape.setAlignment(Qt.AlignCenter)

    def atualizar_alunos(self):
        ano = self.ano_dropdown.currentText()
        self.aluno_dropdown.clear()
        if ano in self.alunos_por_ano:
            alunos = sorted([a[0] for a in self.alunos_por_ano[ano]])
            self.aluno_dropdown.addItems(alunos)
            self.aluno_dropdown.setEnabled(True)

    def abrir_janela_edicao(self):
        if not self.aluno_dropdown.currentText():
            QMessageBox.warning(self, "Atenção", "Selecione um aluno!")
            return
        ano = self.ano_dropdown.currentText()
        nome = self.aluno_dropdown.currentText()
        self.dados_aluno = next((d for n, d in self.alunos_por_ano[ano] if n == nome), None)
        if self.dados_aluno:
            self.janela_edicao = JanelaEdicao(self)
            self.janela_edicao.show()

    # === NOVO: GERA HTML COM DATA ATUAL ===
    def gerar_html(self, dados, modelo=None, incluir_frequencia=False):
        if modelo is None:
            modelo = self.modelo_frequencia_html if incluir_frequencia else self.modelo_html

        hoje = datetime.now()
        sub = {
            "(NOME)": self.padronizar_texto(dados.get("NOME COMPLETO", "")),
            "(PALAVRA)": "nascido" if dados.get("GÊNERO", "").upper() == "M" else "nascida",
            "(DATA)": self.padronizar_texto(dados.get("DATA DE NASCIMENTO", "")),
            "(CIDADE)": self.padronizar_texto(dados.get("NATURALIDADE", "")),
            "(PALAVRA2)": "filho" if dados.get("GÊNERO", "").upper() == "M" else "filha",
            "(PAIS)": self.padronizar_texto(dados.get("NOME DOS PAIS", "")),
            "(PALAVRA3)": "matriculado" if dados.get("GÊNERO", "").upper() == "M" else "matriculada",
            "(ANOTURMA)": f"{dados.get('ANO', '')} - {dados.get('TURMA', '')}",
            "(NIS)": self.padronizar_texto(dados.get("NIS DO ALUNO", "")),
            "(DIA)": str(hoje.day),
            "(MES)": hoje.strftime("%B").lower(),
            "(ANO)": str(hoje.year),
        }

        # Só adiciona frequência se estiver ativada
        if incluir_frequencia:
            sub["(MES1)"] = dados.get("MES1", "")
            sub["(MES2)"] = dados.get("MES2", "")
            sub["(FREQ1)"] = dados.get("FREQ1", "0")
            sub["(FREQ2)"] = dados.get("FREQ2", "0")

        with open(modelo, "r", encoding="utf-8") as f:
            html = f.read()
        for k, v in sub.items():
            html = html.replace(k, v)
        return html

    # === SALVAR COMO PDF (rápido e sem erro) ===
    def salvar_documento(self, dados, incluir_frequencia=False):
        modelo_usado = self.modelo_frequencia_html if incluir_frequencia else self.modelo_html
        if incluir_frequencia and not os.path.exists(modelo_usado):
            QMessageBox.critical(self, "Erro", f"Modelo não encontrado:\n{modelo_usado}")
            return

        html = self.gerar_html(dados, modelo=modelo_usado, incluir_frequencia=incluir_frequencia)
        nome_aluno = dados.get("NOME COMPLETO", "declaracao").strip()
        nome_arquivo = f"declaracao_{nome_aluno.replace(' ', '_').replace('/', '_')}.pdf"
        caminho_pdf = os.path.join(self.caminho_salvamento, nome_arquivo)

        temp_view = QWebEngineView()
        temp_view.setHtml(html, QUrl.fromLocalFile(modelo_usado if incluir_frequencia else self.modelo_html))

        def salvar_pdf(pdf_data):
            try:
                with open(caminho_pdf, "wb") as f:
                    f.write(pdf_data)
                os.startfile(caminho_pdf)
                QMessageBox.information(self, "PDF Salvo!", f"Declaração salva na Área de Trabalho!\n\n{nome_arquivo}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao salvar:\n{e}")
            finally:
                temp_view.deleteLater()

        temp_view.loadFinished.connect(lambda ok: ok and temp_view.page().printToPdf(salvar_pdf))

    def imprimir_documento(self, dados, impressora_nome=None, incluir_frequencia=False):
        modelo_usado = self.modelo_frequencia_html if incluir_frequencia else self.modelo_html
        if incluir_frequencia and not os.path.exists(modelo_usado):
            QMessageBox.critical(self, "Erro", f"Modelo não encontrado:\n{modelo_usado}")
            return

        html = self.gerar_html(dados, modelo=modelo_usado, incluir_frequencia=incluir_frequencia)

        printer = QPrinter()
        printer.setPageSize(QPrinter.A4)
        printer.setOutputFormat(QPrinter.NativeFormat)
        if impressora_nome:
            printer.setPrinterName(impressora_nome)

        view = QWebEngineView()
        view.setHtml(html, QUrl.fromLocalFile(modelo_usado if incluir_frequencia else self.modelo_html))

        def imprimir_quando_carregar(ok):
            if not ok:
                QMessageBox.critical(self, "Erro", "Falha ao carregar o documento.")
                view.deleteLater()
                return

            def imprimir_completado(sucesso):
                if sucesso:
                    QMessageBox.information(self, "Sucesso!", f"Impressão enviada!\n→ {impressora_nome or 'Padrão'}")
                else:
                    QMessageBox.warning(self, "Atenção", "Impressão pode ter falhado. Verifique a impressora.")
                view.deleteLater()

            view.page().print(printer, imprimir_completado)

        view.loadFinished.connect(imprimir_quando_carregar)
        
# === JANELA DE EDIÇÃO (igual à sua, só atualizada para usar os novos métodos) ===
class JanelaEdicao(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Editar Dados do Aluno - Pré-visualização Completa")
        
        # TAMANHO DA JANELA (ajuste aqui se quiser maior/menor)
        self.setFixedSize(1000, 600)

        # ESTILO ESPECÍFICO SÓ PARA ESSA JANELA (fonte maior)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fff8;  /* fundo suave, opcional */
            }
            QLabel {
                font-size: 12px;            /* labels maiores e legíveis */
                font-weight: bold;
                color: #333333;
                min-height: 28px;
            }
            QLineEdit {
                font-size: 12px;            /* campos de texto bem visíveis */
                padding: 10px 14px;
                border: 2px solid #658165;
                border-radius: 8px;
                background: white;
                min-height: 15px;           /* altura mínima pra não achatar */
            }
            QComboBox {
                font-size: 12px;
                padding: 10px 14px;
                border: 2px solid #658165;
                border-radius: 8px;
                background: white;
                min-height: 15px;
            }
            QComboBox::drop-down {
                width: 40px;
                border-left: 2px solid #658165;
            }
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                padding: 12px 24px;
                min-height: 52px;
                border-radius: 8px;
                background-color: #658165;
                color: white;
            }
            QPushButton:hover {
                background-color: #557a57;
            }
            QCheckBox {
                font-size: 15px;
                spacing: 12px;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #658165;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)

        # Layout principal: esquerda (campos) + direita (preview)
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # === ESQUERDA: Campos de edição (fixo) ===
        esquerda = QWidget()
        esquerda.setFixedWidth(540)  # Aumentei um pouco pra ficar mais confortável
        layout_esquerda = QVBoxLayout(esquerda)
        layout_esquerda.setSpacing(14)

        # Impressora
        imp_l = QHBoxLayout()
        imp_l.addWidget(QLabel("IMPRESSORA:"))
        self.imp_combo = QComboBox()
        infos = win32print.EnumPrinters(2)
        self.impressoras_corretas = {}
        for p in infos:
            nome_exibido = p[2]
            nome_real = p[1]
            self.impressoras_corretas[nome_exibido] = nome_real
        nomes_ordenados = sorted(self.impressoras_corretas.keys(), key=str.lower)
        self.imp_combo.addItems(nomes_ordenados)
        try:
            padrao = win32print.GetDefaultPrinter()
            for ex, real in self.impressoras_corretas.items():
                if real == padrao:
                    self.imp_combo.setCurrentText(ex)
                    break
        except: pass
        self.imp_combo.setFixedWidth(320)
        imp_l.addWidget(self.imp_combo)
        layout_esquerda.addLayout(imp_l)

        # Campos editáveis
        self.campos = {}
        campos = ["NOME COMPLETO", "DATA DE NASCIMENTO", "NATURALIDADE", "NOME DOS PAIS", "NIS DO ALUNO"]
        for campo in campos:
            h = QHBoxLayout()
            h.addWidget(QLabel(f"{campo}:"))
            edit = QLineEdit(parent.dados_aluno.get(campo, ""))
            edit.setFixedWidth(320)
            edit.setAlignment(Qt.AlignCenter)
            edit.textChanged.connect(self.atualizar_preview)
            h.addWidget(edit)
            self.campos[campo] = edit
            layout_esquerda.addLayout(h)

        # Checkbox frequência
        self.checkbox_frequencia = QCheckBox("Incluir frequência dos últimos 2 meses")
        self.checkbox_frequencia.setFont(QFont("Arial", 11, QFont.Bold))
        self.checkbox_frequencia.stateChanged.connect(self.mostrar_campos_frequencia)
        self.checkbox_frequencia.stateChanged.connect(self.atualizar_preview)
        layout_esquerda.addWidget(self.checkbox_frequencia)

                # === GRUPO FREQUÊNCIA (agora com título BEM GROSSO e igual aos outros) ===
        self.grupo_frequencia = QGroupBox("FREQUÊNCIA ESCOLAR")
        self.grupo_frequencia.setVisible(False)
        self.grupo_frequencia.setStyleSheet("""
            QGroupBox {
                font-family: Arial;
                font-size: 8pt;           
                font-weight: bold;
                color: #000000;
                border: 2px solid #86b089;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 10px;
                font-weight: 500;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                color: black;
                font-weight: 500;
            }
        """)
        grupo_layout = QFormLayout(self.grupo_frequencia)

        meses = ["← Selecione o Mês →", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

        self.combo_mes1 = QComboBox()
        self.combo_mes1.addItems(meses)
        self.combo_mes2 = QComboBox()
        self.combo_mes2.addItems(meses)

        # ── Lógica de bimestre anterior automática ───────────────────────────────
        mes_atual = datetime.now().month

        # Mapeamento: mês atual → bimestre anterior (os dois meses que devem ser selecionados)
        bimestres_anteriores = {
            4:  ("Fevereiro", "Março"),     # abril → 1º bimestre fechado
            5:  ("Fevereiro", "Março"),     # maio
            6:  ("Abril", "Maio"),          # junho → 2º
            7:  ("Abril", "Maio"),          # julho
            8:  ("Junho", "Agosto"),        # agosto → 3º
            9:  ("Junho", "Agosto"),        # setembro
            11: ("Setembro", "Outubro"),    # novembro → 4º
            12: ("Setembro", "Outubro"),    # dezembro
        }

        # Opção padrão destacada
        opcao_padrao = "← Selecione o Mês →"

        # Se o mês atual está no dicionário, usa o bimestre anterior
        if mes_atual in bimestres_anteriores:
            mes1, mes2 = bimestres_anteriores[mes_atual]
            self.combo_mes1.setCurrentText(mes1)
            self.combo_mes2.setCurrentText(mes2)
        else:
            # Para meses não mapeados (ex: Janeiro, Março, Outubro) → pode deixar em branco ou usar último bimestre
            # Aqui deixamos o mais recente (setembro/outubro) como fallback
            self.combo_mes1.setCurrentText(opcao_padrao)
            self.combo_mes2.setCurrentText(opcao_padrao)

        # ── Campos de frequência (permanece igual) ────────────────────────────────
        self.freq1 = QLineEdit("75")
        self.freq2 = QLineEdit("75")
        self.freq1.setFixedWidth(90)
        self.freq2.setFixedWidth(90)
        self.freq1.setAlignment(Qt.AlignCenter)
        self.freq2.setAlignment(Qt.AlignCenter)

        # Conexões (mantém igual)
        self.combo_mes1.currentTextChanged.connect(self.atualizar_preview)
        self.combo_mes2.currentTextChanged.connect(self.atualizar_preview)
        self.freq1.textChanged.connect(self.atualizar_preview)
        self.freq2.textChanged.connect(self.atualizar_preview)

        # Layout (só ajustei o "→" para ficar mais limpo, mas pode manter o seu)
        row1 = QHBoxLayout()
        row1.addWidget(self.combo_mes1)
        row1.addWidget(QLabel(" → "))
        row1.addWidget(self.freq1)
        row1.addWidget(QLabel("%"))

        row2 = QHBoxLayout()
        row2.addWidget(self.combo_mes2)
        row2.addWidget(QLabel(" → "))
        row2.addWidget(self.freq2)
        row2.addWidget(QLabel("%"))

        grupo_layout.addRow("1º mês:", row1)
        grupo_layout.addRow("2º mês:", row2)
        self.grupo_frequencia.setLayout(grupo_layout)
        layout_esquerda.addWidget(self.grupo_frequencia)

        layout_esquerda.addStretch()

        # Botões
        btns = QHBoxLayout()
        salvar = QPushButton("SALVAR DOCUMENTO")
        salvar.setFont(QFont("Arial", 10, QFont.Bold))
        salvar.setFixedSize(250, 52)
        salvar.clicked.connect(self.salvar)

        imprimir = QPushButton("IMPRIMIR DOCUMENTO")
        imprimir.setFont(QFont("Arial", 10, QFont.Bold))
        imprimir.setFixedSize(250, 52)
        imprimir.clicked.connect(self.imprimir)

        btns.addWidget(salvar)
        btns.addWidget(imprimir)
        layout_esquerda.addLayout(btns)

        # === DIREITA: PRÉ-VISUALIZAÇÃO PERFEITA (DOCUMENTO INTEIRO) ===
        self.preview = QWebEngineView()
        self.preview.setFixedSize(437, 580)  # Largura e altura ideal

        # A MÁGICA: zoom ajustado pra caber o documento inteiro sem scroll
        self.preview.page().setZoomFactor(0.53)

        # Estilo lindo
        self.preview.setStyleSheet("""
            QWebEngineView {
                border: 5px solid #86b089;
                border-radius: 18px;
                background: #f8fff8;
                box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            }
        """)

        # Adiciona no layout
        main_layout.addWidget(esquerda)
        main_layout.addWidget(self.preview, alignment=Qt.AlignCenter)

        # Primeira atualização
        QTimer.singleShot(400, self.atualizar_preview)

    def mostrar_campos_frequencia(self, state):
        self.grupo_frequencia.setVisible(state == Qt.Checked)
        self.atualizar_preview()

    def atualizar_preview(self):
        dados = self.montar_dados()
        incluir_freq = self.checkbox_frequencia.isChecked()
        modelo = self.parent.modelo_frequencia_html if incluir_freq else self.parent.modelo_html
        html = self.parent.gerar_html(dados, modelo=modelo, incluir_frequencia=incluir_freq)
        self.preview.setHtml(html, QUrl.fromLocalFile(modelo))

    def salvar(self):
        dados = self.montar_dados()
        self.parent.salvar_documento(dados, incluir_frequencia=self.checkbox_frequencia.isChecked())
        self.close()

    def imprimir(self):
        dados = self.montar_dados()
        self.parent.imprimir_documento(
            dados,
            impressora_nome=self.imp_combo.currentText(),
            incluir_frequencia=self.checkbox_frequencia.isChecked()
        )
        self.close()

    def montar_dados(self):
        dados = {k: v.text().upper() for k, v in self.campos.items()}
        dados["ANO"] = self.parent.ano_dropdown.currentText()
        dados["TURMA"] = next(d["TURMA"] for n, d in self.parent.alunos_por_ano[
            self.parent.ano_dropdown.currentText()] if n == self.parent.aluno_dropdown.currentText())
        dados["GÊNERO"] = self.parent.dados_aluno.get("GÊNERO", "")

        if self.checkbox_frequencia.isChecked():
            dados["MES1"] = self.combo_mes1.currentText()
            dados["MES2"] = self.combo_mes2.currentText()
            dados["FREQ1"] = self.freq1.text().strip() or "0"
            dados["FREQ2"] = self.freq2.text().strip() or "0"
        return dados

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = GeradorDeclaracao()
    janela.show()
    sys.exit(app.exec_())
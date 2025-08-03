import os
import sys
import time
import tempfile
import requests
import subprocess
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt6.QtCore import QThread, pyqtSignal, Qt


class DownloadThread(QThread):
    """
    Thread para download em background com progresso
    """
    progress_updated = pyqtSignal(int)
    download_completed = pyqtSignal(str)
    download_failed = pyqtSignal(str)
    download_cancelled = pyqtSignal()
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self._cancelled = False
        
    def run(self):
        try:
            response = requests.get(self.url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Obter tamanho total do arquivo
            total_size = int(response.headers.get('content-length', 0))
            
            # Salvar em arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
                downloaded_size = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    # Verificar se foi cancelado
                    if self._cancelled:
                        temp_file.close()
                        os.unlink(temp_file.name)  # Deletar arquivo temporário
                        self.download_cancelled.emit()
                        return
                    
                    if chunk:
                        temp_file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Calcular e emitir progresso
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_updated.emit(progress)
                
                # Verificar se foi cancelado antes de finalizar
                if self._cancelled:
                    temp_file.close()
                    os.unlink(temp_file.name)  # Deletar arquivo temporário
                    self.download_cancelled.emit()
                    return
                
                temp_file.flush()
                file_path = temp_file.name
                
                # Verificar se arquivo foi salvo corretamente
                if not os.path.exists(file_path):
                    self.download_failed.emit("Falha ao salvar arquivo temporário")
                    return
                
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    self.download_failed.emit("Arquivo baixado está vazio")
                    return
                
                self.download_completed.emit(file_path)
                
        except Exception as e:
            self.download_failed.emit(str(e))
    
    def cancel(self):
        """Cancela o download"""
        self._cancelled = True


class Updater:
    """
    Gerencia a verificação e atualização do aplicativo.
    """
    
    def __init__(self, current_version, version_url=None):
        self.current_version = current_version
        # URL do arquivo version.json no GitHub
        self.version_url = version_url or "https://raw.githubusercontent.com/DreamerJP/POS-assistencia/refs/heads/main/version.json"
    
    def check_for_updates(self):
        """
        Verifica se há uma nova versão consultando a URL definida.
        
        Returns:
            dict ou None: Informações da nova versão, se disponível.
        """
        try:
            response = requests.get(self.version_url, timeout=10)
            response.raise_for_status()
            version_info = response.json()
            
            # Compara versões (string comparison funciona para versionamento simples)
            if version_info["version"] > self.current_version:
                return version_info
            return None
            
        except requests.RequestException as e:
            print(f"Erro de rede ao verificar atualizações: {e}")
            return None
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
            return None
    
    def download_and_install(self, download_url, parent_widget=None):
        """
        Faz o download do novo executável e executa a substituização.
        
        Args:
            download_url (str): URL para download do novo executável.
            parent_widget: Widget pai para a janela de progresso.
        """
        try:
            current_exe = sys.executable
            print(f"[DEBUG] Caminho atual: {current_exe}")
            
            # Criar janela de progresso
            progress_dialog = QProgressDialog("Baixando atualização...", "Cancelar", 0, 100, parent_widget)
            progress_dialog.setWindowTitle("Atualização")
            progress_dialog.setModal(True)
            progress_dialog.setAutoClose(False)
            progress_dialog.setAutoReset(False)
            progress_dialog.setMinimumDuration(0)
            
            # Criar thread de download
            download_thread = DownloadThread(download_url)
            
            def on_progress(progress):
                progress_dialog.setValue(progress)
                progress_dialog.setLabelText("Baixando atualização...")
            
            def on_completed(file_path):
                progress_dialog.close()
                print(f"[DEBUG] Download concluído: {file_path}")
                self._install_update(current_exe, file_path)
            
            def on_failed(error):
                progress_dialog.close()
                print(f"[DEBUG] Download falhou: {error}")
                QMessageBox.critical(parent_widget, "Erro de Download", f"Falha ao baixar atualização: {error}")
            
            def on_cancelled():
                progress_dialog.close()
                print("[DEBUG] Download cancelado pelo usuário")
            
            def on_cancel_clicked():
                download_thread.cancel()
            
            # Conectar sinais
            download_thread.progress_updated.connect(on_progress)
            download_thread.download_completed.connect(on_completed)
            download_thread.download_failed.connect(on_failed)
            download_thread.download_cancelled.connect(on_cancelled)
            
            # Conectar cancelamento do diálogo
            progress_dialog.canceled.connect(on_cancel_clicked)
            
            # Iniciar download
            download_thread.start()
            progress_dialog.exec()
            
        except Exception as e:
            print(f"Falha crítica na atualização: {str(e)}")
            QMessageBox.critical(parent_widget, "Erro de Atualização", f"Detalhes: {str(e)}")
    
    def _install_update(self, current_exe, new_exe_path):
        """
        Instala a atualização após o download.
        
        Args:
            current_exe (str): Caminho do executável atual.
            new_exe_path (str): Caminho do novo executável.
        """
        try:
            print(f"[DEBUG] Tamanho do arquivo: {os.path.getsize(new_exe_path)} bytes")
            
            # Gera e valida script de atualização
            bat_content = self.generate_bat_script(current_exe, new_exe_path)
            bat_path = self.write_and_validate_bat(bat_content, current_exe, new_exe_path)
            
            # Executa script de atualização
            print("Iniciando processo de atualização...")
            print(f"[DEBUG] Executando script: {bat_path}")
            print(f"[DEBUG] Executável atual: {current_exe}")
            print(f"[DEBUG] Novo executável: {new_exe_path}")
            
            # Executar script
            subprocess.Popen([bat_path], shell=True)
            
            # Aguarda um momento para o script iniciar
            time.sleep(2)
            
            # Encerra aplicação atual
            sys.exit(0)
            
        except Exception as e:
            print(f"Falha na instalação: {str(e)}")
            QMessageBox.critical(None, "Erro de Instalação", f"Detalhes: {str(e)}")
    
    def generate_bat_script(self, old_exe, new_exe):
        """
        Gera o conteúdo do script BAT para substituição do executável.
        
        Args:
            old_exe (str): Caminho do executável atual.
            new_exe (str): Caminho do novo executável.
        
        Returns:
            str: Conteúdo do script BAT.
        """
        old_exe = os.path.normpath(os.path.abspath(old_exe))
        new_exe = os.path.normpath(os.path.abspath(new_exe))
        
        return f"""@echo off
 setlocal enabledelayedexpansion
 
 :: === DADOS DO PROCESSO ===
 set "OLD_EXE={old_exe}"
 set "NEW_EXE={new_exe}"
 
 echo Iniciando processo de atualizacao...
 
 :: === ENCERRAMENTO DO PROCESSO ===
 for %%I in ("%OLD_EXE%") do set "EXE_NAME=%%~nxI"
 echo Encerrando processo: !EXE_NAME!
 taskkill /IM "!EXE_NAME!" /F >nul 2>&1
 
 :: === AGUARDAR PROCESSO ENCERRAR ===
 timeout /t 3 /nobreak >nul
 
 :: === VALIDACAO DOS ARQUIVOS ===
 if not exist "%NEW_EXE%" (
     echo ERRO: Novo executavel nao encontrado
     echo Caminho: %NEW_EXE%
     pause
     exit /b 1
 )
 
 :: === PROCESSO DE SUBSTITUICAO ===
 echo Substituindo executavel...
 
 :: Obter diretório de destino
 for %%I in ("%OLD_EXE%") do set "TARGET_DIR=%%~dpI"
 
 :: Deletar arquivo antigo se existir
 if exist "%OLD_EXE%" (
     del /F /Q "%OLD_EXE%" >nul 2>&1
     timeout /t 2 /nobreak >nul
 )
 
 :: Copiar novo executável diretamente
 copy /Y "%NEW_EXE%" "%OLD_EXE%" >nul 2>&1
 if %ERRORLEVEL% EQU 0 (
     echo Copia realizada com sucesso
     goto reiniciar
 )
 
 :: Se copia falhou, tentar mover
 move /Y "%NEW_EXE%" "%OLD_EXE%" >nul 2>&1
 if %ERRORLEVEL% EQU 0 (
     echo Movimento realizado com sucesso
     goto reiniciar
 )
 
 echo ERRO: Falha ao copiar executavel
 pause
 exit /b 1
 
 :reiniciar
 :: === REINICIALIZACAO ===
 echo Atualizacao concluida! Reiniciando aplicacao...
 timeout /t 2 /nobreak >nul
 
 :: Tentar iniciar o aplicativo
 start "" "%OLD_EXE%"
 if %ERRORLEVEL% NEQ 0 (
     echo ERRO: Falha ao reiniciar aplicacao
     echo Tentando executar diretamente...
     "%OLD_EXE%"
 )
 
 :: === LIMPEZA ===
 echo Limpando arquivos temporarios...
 timeout /t 2 /nobreak >nul
 
 :: Deletar apenas o arquivo temporário específico que foi baixado
 if exist "%NEW_EXE%" (
     echo Deletando arquivo temporario: %NEW_EXE%
     del /F /Q "%NEW_EXE%" >nul 2>&1
 )
 
 :: Deletar o próprio script BAT
 del /F /Q "%~f0" >nul 2>&1
 
 echo Limpeza concluida!
 exit /b 0
 """
    
    def write_and_validate_bat(self, content, old_exe, new_exe):
        """
        Escreve e valida o script BAT.
        
        Args:
            content (str): Conteúdo do script.
            old_exe (str): Caminho do executável atual.
            new_exe (str): Caminho do novo executável.
        
        Returns:
            str: Caminho do script BAT criado.
        """
        old_exe = os.path.normpath(os.path.abspath(old_exe))
        new_exe = os.path.normpath(os.path.abspath(new_exe))
        bat_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
        
        # Escreve com codificação ANSI (sem BOM) para compatibilidade com Windows
        try:
            with open(bat_path, "w", encoding="cp1252") as f:
                f.write(content)
            
            # Validação crítica
            with open(bat_path, "r", encoding="cp1252") as f:
                content_read = f.read()
                if old_exe not in content_read or new_exe not in content_read:
                    raise ValueError("Falha na validação do script de atualização")
            
            print(f"[DEBUG] Script BAT criado em: {bat_path}")
            return bat_path
            
        except Exception as e:
            raise ValueError(f"Erro ao criar script de atualização: {str(e)}")
    
    def check_for_updates_with_retry(self, max_retries=3):
        """
        Verifica atualizações com retry automático.
        
        Args:
            max_retries (int): Número máximo de tentativas.
        
        Returns:
            dict ou None: Informações da nova versão, se disponível.
        """
        for attempt in range(max_retries):
            try:
                return self.check_for_updates()
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Backoff exponencial
        return None 
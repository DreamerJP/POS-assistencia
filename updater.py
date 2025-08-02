import os
import sys
import time
import tempfile
import requests
import subprocess
from PyQt6.QtWidgets import QMessageBox


class Updater:
    """
    Gerencia a verificação e atualização do aplicativo.
    """
    
    def __init__(self, current_version, version_url=None):
        self.current_version = current_version
        # URL do arquivo version.json no GitHub
        self.version_url = version_url or "https://raw.githubusercontent.com/DreamerJP/POS-assitencia/main/version.json"
    
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
    
    def download_and_install(self, download_url):
        """
        Faz o download do novo executável e executa a substituição.
        
        Args:
            download_url (str): URL para download do novo executável.
        """
        try:
            current_exe = sys.executable
            print(f"[DEBUG] Caminho atual: {current_exe}")
            
            # Download do novo executável
            print("Baixando atualização...")
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
            
            # Salva em arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
                temp_file.write(response.content)
                new_exe_path = temp_file.name
                print(f"[DEBUG] Novo executável salvo em: {new_exe_path}")
            
            # Gera e valida script de atualização
            bat_content = self.generate_bat_script(current_exe, new_exe_path)
            bat_path = self.write_and_validate_bat(bat_content, current_exe, new_exe_path)
            
            # Executa script de atualização
            print("Iniciando processo de atualização...")
            subprocess.Popen(
                [bat_path],
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            
            # Aguarda um momento para o script iniciar
            time.sleep(2)
            
            # Encerra aplicação atual
            sys.exit(0)
            
        except requests.RequestException as e:
            print(f"Erro de download: {str(e)}")
            QMessageBox.critical(None, "Erro de Download", f"Falha ao baixar atualização: {str(e)}")
        except Exception as e:
            print(f"Falha crítica na atualização: {str(e)}")
            QMessageBox.critical(None, "Erro de Atualização", f"Detalhes: {str(e)}")
    
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
chcp 65001 >nul
setlocal enabledelayedexpansion

:: === DADOS DO PROCESSO ===
set "OLD_EXE={old_exe}"
set "NEW_EXE={new_exe}"

echo Iniciando processo de atualizacao...

:: === ENCERRAMENTO DO PROCESSO ===
for %%I in ("%OLD_EXE%") do set "EXE_NAME=%%~nxI"
echo Encerrando processo: !EXE_NAME!
taskkill /IM "!EXE_NAME!" /F >nul 2>&1

:: === VALIDACAO DOS ARQUIVOS ===
if not exist "%OLD_EXE%" (
    echo ERRO: Executavel original nao encontrado
    echo Caminho: %OLD_EXE%
    pause
    exit /b 1
)

if not exist "%NEW_EXE%" (
    echo ERRO: Novo executavel nao encontrado
    echo Caminho: %NEW_EXE%
    pause
    exit /b 1
)

:: === PROCESSO DE SUBSTITUICAO ===
echo Substituindo executavel...
set "MAX_TENTATIVAS=10"

:loop_substituicao
if !MAX_TENTATIVAS! LEQ 0 (
    echo ERRO: Numero maximo de tentativas excedido
    pause
    exit /b 1
)

del /F /Q "%OLD_EXE%" >nul 2>&1

if exist "%OLD_EXE%" (
    echo Aguardando liberacao do arquivo... (Tentativa: !MAX_TENTATIVAS!)
    timeout /t 1 /nobreak >nul
    set /a MAX_TENTATIVAS-=1
    goto loop_substituicao
)

:: === MOVIMENTACAO DO ARQUIVO ===
move /Y "%NEW_EXE%" "%OLD_EXE%" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao mover novo executavel
    pause
    exit /b 1
)

:: === REINICIALIZACAO ===
echo Atualizacao concluida! Reiniciando aplicacao...
timeout /t 2 /nobreak >nul
start "" "%OLD_EXE%"

:: === LIMPEZA ===
timeout /t 3 /nobreak >nul
del /F /Q "%~f0" >nul 2>&1

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
        
        # Escreve com codificação UTF-8 com BOM
        try:
            with open(bat_path, "w", encoding="utf-8-sig") as f:
                f.write(content)
            
            # Validação crítica
            with open(bat_path, "r", encoding="utf-8-sig") as f:
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
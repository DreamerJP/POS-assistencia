# POS - Check-list Pós-Instalação Fibra Óptica

Sistema de gerenciamento para check-lists de pós-instalação de fibra óptica com controle de pendências.

## 📋 Funcionalidades

- **Check-list Estruturado**: Formulário completo para validação pós-instalação
- **Gerenciamento de Pendências**: Salvar, carregar e finalizar pendências
- **Validação Visual**: Campos obrigatórios com indicação visual
- **Geração de Relatórios**: Relatório padronizado para instalações
- **Interface Responsiva**: Design minimalista e intuitivo

## ⚡ Instalação

1. Faça o download do arquivo `POS.exe`
2. Execute o arquivo (não requer instalação)
3. O programa criará automaticamente o arquivo `checklist_pendencias.json` para armazenar dados

## 🔧 Uso

### Check-list Principal
1. Preencha o nome do técnico
2. Complete os campos obrigatórios (indicados por bordas vermelhas quando vazios)
3. Clique em "Gerar Relatório" para criar o relatório final
4. Use "Salvar Pendência" para salvar trabalhos incompletos

### Gerenciamento de Pendências
- **Carregar**: Carrega uma pendência selecionada no formulário
- **Finalizar**: Marca pendência como concluída
- **Excluir**: Remove pendência da lista
- **Editar**: Clique diretamente nas células para editar

## 📋 Campos do Check-list

| Campo | Descrição |
|-------|-----------|
| **1 - Comissão** | Comissão técnico (120) |
| **2 - Comodato** | Equipamento em comodato |
| **3 - Acesso Remoto** | Configuração de acesso + senha |
| **4 - IP/MAC** | Validação de conectividade |
| **5 - Potência** | Sinais RX/TX da fibra |
| **6 - Instalação** | Padrão de instalação |
| **7 - Localização** | Atualização no sistema |
| **8 - Foto + GPS** | Documentação visual |

## 💾 Arquivos Gerados

- `checklist_pendencias.json`: Armazena pendências salvas
- `Localização GPS [nome].txt`: Arquivos de GPS gerados

## 🔄 Atualizações

O sistema verificará automaticamente por atualizações. Para atualizações manuais, baixe a versão mais recente do repositório.

## 🛠️ Tecnologias

- Python 3.x
- PyQt6
- JSON para persistência de dados

## 📄 Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**Desenvolvido para otimização de processos de pós-instalação de fibra óptica**

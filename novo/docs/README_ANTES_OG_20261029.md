# LittleTec Studio

> **Estado confirmado em 29/10/2026:** desktop 1.1.0 e Web 0.2.0 funcionam em uso
> real para mapeamento, troca de cores e aplicação de mudanças, conforme o usuário.
> USB no Web usa a ponte local Windows; Pages/HTML estático oferecem o editor.
> [Estado atual](../../novo/docs/ESTADO_ATUAL.md) · [Documentação](../../novo/docs/README.md).

Seu teclado macro 12+2, do seu jeito. Configurador próprio em português para Windows x64, com reconhecimento direto de teclas, presets para os 2 knobs giratórios, ações rápidas de mídia e controle de iluminação LED.

**[Baixar LittleTec-Windows-x64.zip — Windows 64 bits](https://github.com/thegodKoDDa/littletec/releases/latest/download/LittleTec-Windows-x64.zip)** · **[Versão Web & Online (GitHub Pages)](https://github.com/thegodKoDDa/littletec-web)** · [Todas as versões](https://github.com/thegodKoDDa/littletec/releases) · [Licença ISC](../../LICENSE)

[![Verificações](https://github.com/thegodKoDDa/littletec/actions/workflows/ci.yml/badge.svg)](https://github.com/thegodKoDDa/littletec/actions/workflows/ci.yml)
[![Licença ISC](https://img.shields.io/badge/licen%C3%A7a-ISC-blue.svg)](LICENSE)

> [!NOTE]
> **Versão Web disponível & Aviso sobre a interface:**
> - Uma versão web moderna, responsiva e com feedback em tempo real está disponível no projeto **[LittleTec Web](https://github.com/thegodKoDDa/littletec-web)**, podendo ser usada diretamente no navegador pelo **[GitHub Pages](https://thegodkodda.github.io/littletec-web/)** ou baixada em pacote HTML portátil.
> - **Aviso de desenvolvimento:** A interface visual atual em PySide6/QML deste aplicativo desktop está plenamente funcional e estável, mas está sujeita a alterações futuras planejadas, com a futura migração e unificação definitiva para o design system da versão Web.

## Teclado de referência compatível

Este software foi desenvolvido, engenharia-reversa e validado especificamente para o mini teclado mecânico programável de **12 teclas + 2 botões giratórios (knobs)** com controlador **WCH CH57x**:

- **Link de referência do modelo utilizado (AliExpress)**: [Mini Teclado Mecânico Programável 12 Teclas + 2 Knobs RGB USB Type-C (Item 1005006437127027)](https://pt.aliexpress.com/item/1005006437127027.html)
- **Identificação USB HID**: `VID_1189&PID_8842` (`0x1189:0x8842`, Interface `MI_00`, Usage Page `0xFF00`, Usage `0x01`, relatórios de 65 bytes com Report ID `0x03`)
- **Controlador físico**: WCH CH57x (memória interna flash persistente para 3 camadas independentes)
- **Layout físico**: 12 teclas mecânicas (`Tecla 01` a `Tecla 12`) + 2 encoders rotativos clicáveis (`Knob 1` e `Knob 2`, cada um com giro à esquerda `↶`, clique central `●` e giro à direita `↷`, totalizando 18 posições por camada e 54 posições nas 3 camadas)
- **Iluminação LED nativa no chip**: 7 cores físicas fixas (`Vermelho`, `Laranja`, `Amarelo`, `Verde`, `Ciano`, `Azul`, `Roxo`) e 6 modos de efeito gravados no firmware (`Desligado`, `Estático`, `Respiração`, `Ciclo Automático`, `Onda ao Pressionar`, `Acender Tecla ao Pressionar`)

## Recursos

- **Reconhecimento direto pelo teclado principal**: clique em qualquer tecla ou posição de knob na tela e pressione a tecla ou combinação desejada no seu próprio teclado (`4`, `Ctrl+C`, `Ctrl+V`, `Ctrl+Shift+M`, `F13–F24`, etc.), com opção de auto-avançar.
- **Painel completo para os 2 Knobs (`Knob 1` e `Knob 2`)**: visualização simultânea de `↶ Esq.`, `● Clique` e `↷ Dir.`, menu rápido `Preset ▾` com 12 perfis prontos (Volume & Mudo, Controle de Mídia, Zoom, Navegação de Abas, Linha do Tempo/Vídeo, Desfazer/Salvar/Refazer, Scroll do Mouse, Desktops Virtuais, Brilho da Tela, Navegação Vertical, Rolagem de Página e Tamanho do Pincel), inversão de sentido (`⇄ Inverter ↶/↷`), troca rápida `Giro 1 ↔ 2` e replicação nas 3 camadas.
- **Ações rápidas em 1 clique para qualquer tecla ou giro**: atribua `Faixa anterior`, `Reproduzir/pausar`, `Próxima faixa`, `Volume +/−`, `Silenciar`, `Copiar`, `Colar`, `Recortar`, `Desfazer`, `Salvar`, `Print (Win+Shift+S)`, `Mudo Discord` ou `Calculadora` em qualquer posição.
- **Sequências de até 20 etapas e digitação de texto/números**: crie macros de teclado com reordenação de etapas, modificadores independentes ou digite um texto/número (ex.: `1234` + `Enter`) para atribuir automaticamente.
- **Templates prontos de camada**: preencha as 18 posições da camada ativa em 1 clique (*Produtividade & Edição*, *Multimídia, Jogos & Discord*, *Navegador & Web*, *Teclado Numérico 0–9* e *Edição de Vídeo*) ou clone uma camada para outra.
- **Controle de iluminação LED sem complicações**: seleção direta das 7 cores físicas e 6 modos nativos do chip por camada (com envio automático em 1 clique ou aplicação simultânea nas 3 camadas).
- **Segurança de dados e backups automáticos**: cada leitura e gravação salva uma cópia bruta verificada em `%LOCALAPPDATA%\LittleTec\captures` e confere a releitura dos registros; em caso de falha de comunicação, restaura automaticamente a configuração anterior.

## Começar

### Baixar e usar no Windows — recomendado

1. **[Baixe o LittleTec-Windows-x64.zip](https://github.com/thegodKoDDa/littletec/releases/latest/download/LittleTec-Windows-x64.zip)**.
2. Extraia a pasta em um diretório local (por exemplo, `C:\LittleTec\`) e abra **`LittleTec.exe`** (mantenha a pasta `_internal` ao lado do executável). Não é necessário instalar Python nem drivers especiais.
3. Com o teclado `1189:8842` conectado via USB, o aplicativo lê automaticamente as 3 camadas ao abrir.

### Executar a partir do código-fonte (Windows x64)

Requisitos: **Python 3.13 (64 bits)** no Windows.

```powershell
git clone https://github.com/thegodKoDDa/littletec.git
cd littletec\novo
powershell -ExecutionPolicy Bypass -File tools\setup_qt_windows.ps1
.\.venv-qt-windows\Scripts\python.exe tools\studio_qt.py
```

### Gerar seu próprio executável Windows

Com o ambiente `.venv-qt-windows` preparado:

```powershell
.\.venv-qt-windows\Scripts\python.exe tools\build_qt_windows.py
```

O pacote compilado é gerado em `novo/dist/LittleTec.exe` junto da pasta `novo/dist/_internal/`.

## Desenvolvimento

A arquitetura separa completamente o domínio/protocolo da interface gráfica:

- **Domínio e protocolo (`novo/src/littletec/`)**: codificação e decodificação pura dos registros de 50 bytes e relatórios USB HID de 65 bytes, validados contra 206 vetores reais do hardware.
- **Interface (`novo/src/littletec/ui_qt/`)**: PySide6 / Qt Quick (QML) com operações USB serializadas em `QThread` (`device_worker.py`), mantendo a interface responsiva.

Para executar a suíte de testes unitários (Linux ou Windows, sem exigir o teclado conectado):

```bash
cd novo
python3 -m unittest discover -s tests -v
```

| Diretório | Conteúdo |
| --- | --- |
| `novo/src/littletec/` | Protocolo USB HID (`1189:8842`), catálogo, perfis, sessão e serviços de leitura/escrita |
| `novo/src/littletec/ui_qt/` | Controlador Qt, worker assíncrono e componentes visuais QML |
| `novo/tests/` | 79 testes automatizados e vetores reais de protocolo (`fixtures/`) |
| `novo/tools/` | Scripts de build Windows (`build_qt_windows.py`), diagnóstico HID e verificação |
| `novo/docs/` | Especificação técnica do protocolo recuperado (`PROTOCOLO.md`) e integração dos encoders (`ENCODERS_INTEGRACAO.md`) |

## Documentação

- [Guia rápido do Studio](../../novo/README.md)
- [Protocolo USB HID 1189:8842](../../novo/docs/PROTOCOLO.md)
- [Endereçamento e integração dos Knobs giratórios](../../novo/docs/ENCODERS_INTEGRACAO.md)
- [Histórico de versões](../../CHANGELOG.md)
- [Guia de contribuição](../../CONTRIBUTING.md)

## Licença

[ISC](../../LICENSE). Bibliotecas de terceiros (PySide6/Qt e HIDAPI) conservam suas respectivas licenças em [`novo/licenses/`](../../novo/licenses/).

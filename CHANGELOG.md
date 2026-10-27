# Changelog

## 1.1.0 — 2026-10-27

### Adicionado

- **Reconhecimento direto pelo teclado principal**: ao selecionar qualquer tecla ou posição de giro, basta pressionar a tecla ou atalho desejado no próprio teclado (`4`, `Ctrl+C`, `Ctrl+V`, `Ctrl+Shift+M`, etc.), com opção de auto-avançar entre posições.
- **Painel dedicado aos 2 Knobs (Giratório 1 e Giratório 2)**: cartões individuais visíveis para `↶ Esq.`, `● Clique` e `↷ Dir.`, menu rápido `Preset ▾` com 12 perfis completos de giro (Volume, Mídia, Zoom, Abas, Vídeo, Desfazer/Refazer, Scroll do Mouse, Desktops Virtuais, Brilho, Navegação Vertical, Página e Pincel), inversão de sentido (`⇄ Inverter ↶/↷`), troca entre Giro 1 ↔ Giro 2 e replicação nas 3 camadas.
- **Ações rápidas em 1 clique e templates de camada**: atribuição imediata de controles de mídia (`Faixa anterior`, `Reproduzir/pausar`, `Próxima faixa`, `Volume`, `Silenciar`) e atalhos para qualquer uma das 12 teclas ou 2 knobs, além de 5 templates completos de camada e digitação de sequências de texto/números.
- **Iluminação LED calibrada para o controlador WCH CH57x (`1189:8842`)**: suporte às 7 cores físicas nativas e aos 6 modos de efeito gravados no firmware por camada, com envio direto em 1 clique e opção de aplicar a mesma cor nas 3 camadas.

### Corrigido

- Eliminação de piscadas visuais na grade de 12 teclas e na caixa de captura de teclado ao clicar em botões.
- Remoção de diálogos bloqueantes desnecessários ao limpar posições ou fechar o aplicativo após gravar no hardware.
- Desativação de cache obsoleto de QML e sincronização automática para execução local no Windows.

## 1.0.0 — 2026-10-27

### Adicionado

- Interface **LittleTec Studio** em Python + PySide6 / Qt Quick (QML) com comunicação USB HIDAPI validada no Windows x64 para o teclado mecânico programável 12 teclas + 2 knobs (`VID_1189&PID_8842`).
- Leitura e escrita verificada dos 72 registros nas 3 camadas (12 teclas + 6 posições dos 2 giratórios), com cópia de segurança automática e restauração em caso de falha de comunicação.

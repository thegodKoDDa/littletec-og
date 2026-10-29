> **Arquivo LittleTec OG (29/10/2026):** desenvolvimento encerrado. Conteúdo
> preservado para uso/consulta do Qt 1.1.0. O trabalho ativo segue no
> [LittleTec Studio](https://github.com/thegodKoDDa/littletecstudio).
> A antiga cópia Web local está no histórico do Studio; caminhos antigos abaixo
> descrevem a organização anterior.

# LittleTec Studio 1.1

> **Estado confirmado em 29/10/2026:** desktop 1.1.0 e Web 0.2.0 funcionam em uso
> real para mapeamento, troca de cores e aplicação de mudanças, conforme o usuário.
> USB no Web usa a ponte local Windows; Pages/HTML estático oferecem o editor.
> [Estado atual](docs/ESTADO_ATUAL.md) · [Documentação](docs/README.md).

Interface Qt própria em português para configurar o teclado mecânico **12 teclas + 2 knobs giratórios (`1189:8842`)**, utilizando o firmware nativo do controlador WCH CH57x.

- **Modelo de referência**: [Mini Teclado Mecânico Programável 12 Teclas + 2 Knobs RGB (AliExpress)](https://pt.aliexpress.com/item/1005006437127027.html)

## Abrir no Windows

Abra **`Abrir-LittleTec.cmd`** ou **`dist/LittleTec.exe`**. Não precisa instalar Python. Mantenha a pasta **`dist/_internal/`** junto do executável.

O aplicativo identifica o modelo `1189:8842` e lê o teclado em segundo plano ao abrir. O botão **Ler teclado** permite atualizar a leitura a qualquer momento.

## Configurar teclas e os 2 Knobs

1. Em **Mapeamento**, escolha a camada (`1`, `2` ou `3`) e clique em uma das **12 teclas** ou em uma das posições dos **2 Knobs** (`↶ Esq.`, `● Clique` ou `↷ Dir.`).
2. **Para gravar direto pelo seu teclado**: com a opção **⌨ Capturar do meu teclado** marcada, basta pressionar qualquer tecla ou atalho (`4`, `Ctrl+C`, `Ctrl+V`, etc.) no seu teclado principal.
3. **Para configurar um Knob inteiro em 1 clique**: clique em **`Preset ▾`** no cabeçalho do **KNOB / GIRO 1** ou **KNOB / GIRO 2** e escolha um dos 12 presets prontos (*Volume & Mudo*, *Controle de Mídia*, *Zoom*, *Navegação de Abas*, *Vídeo*, *Scroll do Mouse*, etc.). Use **`⇄ Inverter ↶/↷`** se quiser inverter o sentido de rotação.
4. **Ações rápidas e catálogo**: use a barra de **Ações Rápidas em 1 Clique** ou o catálogo inferior para atribuir controles de mídia, mouse, texto/números, atrasos ou templates completos de camada.
5. Clique em **Aplicar mapeamento** para gravar no teclado. O resultado é relido e conferido automaticamente.

## Trocar iluminação LED

1. Abra **Iluminação** e selecione a camada (`1`, `2` ou `3`).
2. Escolha uma das **7 cores físicas** nativas do chip (`Vermelho`, `Laranja`, `Amarelo`, `Verde`, `Ciano`, `Azul`, `Roxo`) e um dos **6 modos de efeito** (`Modo 0 · Desligado` a `Modo 5 · Acender ao Pressionar`).
3. Com **Aplicar automaticamente ao clicar** marcado, a cor/efeito é enviada imediatamente ao teclado. Use **Aplicar esta cor nas 3 Camadas** para padronizar todas as camadas de uma vez.

## Testes e build

```bash
python3 -m unittest discover -s tests -v
.venv-qt-windows/Scripts/python.exe tools/studio_qt.py
.venv-qt-windows/Scripts/python.exe tools/build_qt_windows.py
```

Detalhes técnicos do protocolo em [docs/PROTOCOLO.md](docs/PROTOCOLO.md) e [docs/ENCODERS_INTEGRACAO.md](docs/ENCODERS_INTEGRACAO.md).

# Arquitetura atual — 29/10/2026

Estado do produto em [ESTADO_ATUAL.md](../ESTADO_ATUAL.md). **Studio desktop
1.1.0 e Web 0.2.0 funcionam em uso real**, inclusive mapeamento, cores e aplicação.
A migração Tk → Qt e a integração USB estão concluídas.

## Núcleo Python

| Responsabilidade | Módulos em `novo/src/littletec/` |
| --- | --- |
| Catálogo e ações | `catalog.py` |
| Perfis JSON v2 e migração v1 | `profile.py` |
| Registros e pacotes, sem I/O | `protocol.py` |
| Edição, seleção e histórico sem GUI/USB | `editor_session.py` |
| Identidade, leitura e cópias | `identity.py`, `config_read.py`, `device_service.py` |
| Casos de uso atuais | `configuration_service.py` |
| Transporte LED e utilitários legados | `lighting_service.py` |
| Pacotes, comparação e fluxo legado de teclas | `write_service.py`, `write_trial.py` |
| Diagnóstico | `diagnostics.py` e auxiliares Windows em `tools/` |

`ConfigurationService` coordena cópia recente, validação de origem, aplicação,
releitura e tentativa de retorno em falha. Usa utilitários dos serviços anteriores
sem impor a política antiga de recibos e confirmações visuais no uso normal.
O transporte atual aceita teclas 1–12 e giros 16–21. Registros opacos são
preservados e sua substituição não interpretada é recusada.

O carregamento dinâmico de auxiliares em `tools/` ainda existe. As pastas
`application/` e `infrastructure/` propostas no plano antigo não são a organização
implementada; sua criação não é uma pendência necessária para o produto funcionar.

## Desktop Qt

```text
QML → StudioController → DeviceWorker (QObject em QThread)
    → ConfigurationService → HIDAPI Windows → MI_00 / 1189:8842
```

- `ui_qt/controller.py`: propriedades, comandos, perfis, revisão e adaptação da sessão.
- `ui_qt/device_worker.py`: executor serial fora da thread visual.
- `ui_qt/qml/Main.qml` e `components/`: mapeamento, iluminação, perfis e diagnóstico.
- `ui_qt/launcher.py`: inicialização; `tools/studio_qt.py` é a entrada normal.

QML não constrói pacotes USB. A sessão local e o snapshot são separados para
preservar edições durante I/O. O launcher normal lê o aparelho ao abrir;
`--offline` impede apenas essa conexão automática.

Tk permanece como fonte local histórica (`app.py`, `board.py`, `theme.py`,
`lighting_dialog.py`), fora do build Qt. Não é o produto atual.

## Web

```text
React → Next /api/device → ponte Python Windows em loopback
                         ↳ relay por stdin quando executado no WSL/NAT
Ponte → ConfigurationService → HIDAPI → MI_00 (configuração)
      → Windows Raw Input → MI_01 (entrada ao vivo)
```

A ponte valida comandos, serializa operações e exige revisão do snapshot para
não aplicar a partir de uma aba desatualizada. O token permanece entre os
processos locais. O monitor ao vivo associa eventos ao mapeamento lido, respeita
origens ambíguas e não bloqueia os comandos do Windows.

`web/` importa o núcleo do desktop; o repositório independente `littletec-web`
inclui sua cópia em `bridge/core/littletec/`. Não há sincronização automática.
Pages e HTML estático oferecem edição de perfis sem a ponte USB.

## Estado e persistência

- Arquivo/biblioteca salvos, rascunho e configuração aplicada são conceitos distintos.
- LED: seleção local, último comando enviado ou estado desconhecido; não há readback.
- Perfil v1/v2 e campos opacos preservados; modelo de rascunho não implica suporte USB.
- Capturas guardam os 72 relatórios reais; normalização de IDs de giros acontece
  somente na cópia de interpretação, conforme [protocolo](../PROTOCOLO.md).
- Falha real não é sucesso. Retorno pode ser tentado, mas não é garantido se o
  dispositivo estiver inacessível. Cópias não incluem firmware nem estado LED interno.

## Distribuição

`tools/build_qt_windows.py` usa PyInstaller, entrada `src/desktop_qt.py`, coleta
QML, HIDAPI, auxiliares Windows e licenças e promove o pacote para `dist/`.
O artefato atual é `dist/LittleTec.exe` com `_internal/` ao lado.
A procedência Qt 1.0 é histórica e não fixa o hash do executável 1.1.

Convergência visual desktop/Web está registrada como direção futura; não foi
implementada nesta atualização documental. A decisão original foi preservada em
`../historico/ARQUITETURA_20261027.md` (arquivo local, fora do Git).

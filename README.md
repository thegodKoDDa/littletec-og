# LittleTec OG — desktop preservado

**Desenvolvimento encerrado em 29/10/2026. Este projeto não receberá novas
funcionalidades ou correções.** O aplicativo Qt 1.1.0 continua preservado e
funcional; todo o trabalho futuro está no **[LittleTec Studio](https://github.com/thegodKoDDa/littletecstudio)**,
que reúne Web e o novo Desktop com interface compartilhada.

**[Baixar desktop OG 1.1.0](https://github.com/thegodKoDDa/littletec-og/releases/download/v1.1.0/LittleTec-Windows-x64.zip)** ·
**[Novo LittleTec Studio](https://github.com/thegodKoDDa/littletecstudio)** ·
**[Web do Studio](https://thegodkodda.github.io/littletecstudio/)** ·
[Licença ISC](LICENSE)

## Produto de referência e identificação USB

**[Mini Teclado Mecânico Programável — 12 teclas + 2 knobs, RGB e USB Type-C (AliExpress, item 1005006437127027)](https://pt.aliexpress.com/item/1005006437127027.html)**

Esse é o produto de referência utilizado no projeto. O suporte USB é específico
para a variante observada **12+2, variante 0**; semelhança visual ou o mesmo
VID/PID em outro aparelho não garante compatibilidade.

| Característica | Referência do projeto |
| --- | --- |
| Controlador | WCH CH57x |
| USB VID:PID | **`1189:8842`** (`0x1189:0x8842`, `VID_1189&PID_8842`) |
| Interface de configuração | `MI_00`, HID de fornecedor, Usage Page `0xFF00`, Usage `0x01` |
| Relatórios de configuração | 65 bytes, Report ID `0x03` |
| Camadas | Três camadas independentes |
| Teclas | 12 teclas mecânicas, `Tecla 01` a `Tecla 12` |
| Giratórios | Dois knobs; esquerda, clique e direita independentes em cada um |
| Posições configuráveis | 18 por camada, 54 nas três camadas |
| Iluminação | Sete cores nativas: vermelho, laranja, amarelo, verde, ciano, azul e roxo |
| Modos LED | Desligado, estático, respiração, ciclo automático, onda ao pressionar e acender tecla ao pressionar |

No Studio, a entrada ao vivo usa a interface `MI_01` por Windows Raw Input;
a configuração usa HIDAPI na `MI_00`. O OG preserva sua interface Qt, sem o
monitor ao vivo do Studio. LED não tem readback conhecido: prévia e último
comando enviado não representam leitura do estado interno.

## O que fica preservado

- Nosso primeiro desktop: Python + PySide6/Qt Quick/QML + HIDAPI, Windows x64.
- Versão **1.1.0**, com mapeamento, cores, aplicação e giratórios funcionais
  confirmados pelo usuário em uso real.
- Fontes, testes, documentação, histórico Git e release publicada.
- No diretório local: `novo/dist/LittleTec.exe` e `_internal`, ambientes, capturas
  e os 70 arquivos do programa original do fabricante em `original/`.

Os originais do fabricante não são o aplicativo desenvolvido aqui. Seus binários
continuam intactos no arquivo local e não são incluídos neste repositório público.
Capturas, análise e ambientes também permanecem locais.

## Abrir o OG

No checkout local, abrir `Abrir-OG.cmd` ou `novo/Abrir-LittleTec.cmd`. O lançador
já existente prepara a distribuição Qt no Windows. Na versão baixada, extrair o
ZIP em uma pasta Windows e abrir `LittleTec.exe`, mantendo `_internal` ao lado.
O Qt faz leitura automática ao abrir; essa é a operação preservada da versão.

Não é necessário instalar Python para usar o pacote pronto. O modelo USB é
`1189:8842`, **12 teclas + 2 giratórios, variante 0**. Perfis v1/v2 e dados opacos
continuam preservados. LED não tem readback: último envio não é leitura interna.

## Organização e continuidade

| Diretório | Conteúdo |
| --- | --- |
| `original/` | Programa do fabricante, somente no arquivo local |
| `novo/src/` | Fontes do desktop Qt preservado |
| `novo/dist/` | Executável Qt e dependências, somente local |
| `novo/tests/` | Testes puros e vetores |
| `novo/docs/` | Documentação técnica e registros históricos |
| `novo/captures/`, `novo/analysis/` | Evidências locais preservadas |

A cópia Web antes existente em `web/` foi transferida para a pasta local do
Studio, em `.local/legado/web-interno-20261029/`, incluindo suas evidências.
Apenas caches regeneráveis foram removidos. Ela não é uma segunda base ativa.

O diretório OG chama-se `littletec-og`; o projeto ativo está em `littletec-studio`.
Os históricos Git e as releases anteriores foram mantidos durante a renomeação.

Para desenvolver, relatar problemas atuais ou baixar o novo `.exe`, use o
[LittleTec Studio](https://github.com/thegodKoDDa/littletecstudio). Este repositório
será mantido arquivado para consulta e uso do desktop antigo.

## Referência histórica

- [README anterior completo](novo/docs/README_ANTES_OG_20261029.md).
- [Guia do desktop Qt](novo/README.md).
- [Protocolo recuperado](novo/docs/PROTOCOLO.md).
- [Histórico de versões](CHANGELOG.md).
- [Índice documental](novo/docs/README.md).

A confirmação de funcionamento não é um laudo de todos os efeitos ou de
persistência após reconexão. Testes físicos não são exigidos por rotina.

# Estado atual — LittleTec

Atualizado em **29/10/2026**. Referência de estado do desktop e de sua relação
com o Web. Relatos anteriores permanecem como histórico.

## Funcionamento confirmado

O usuário confirmou que **desktop e, principalmente, Web estão funcionando
normalmente: mapeando, trocando cores e aplicando mudanças no teclado**.
É confirmação de uso real. Não tratar o desktop como prévia offline nem a
integração Web local como apenas simulador. Não exigir novos ensaios por rotina.

| Aplicação | Versão publicada | Commit da versão | Main consultada em 29/10/2026 |
| --- | --- | --- | --- |
| Studio desktop | `v1.1.0` | `f234995` | `eaa6f36` |
| Web | `v0.2.0` | `256e0ce` | `7f0bb11` |

Os commits posteriores às versões atualizam a documentação sobre a relação entre
os projetos e a convergência visual futura. Não representam novas versões do produto.
Fontes: [desktop](https://github.com/thegodKoDDa/littletec) e
[Web](https://github.com/thegodKoDDa/littletec-web).

## Mapa local

| Caminho, a partir da raiz desktop | Conteúdo |
| --- | --- |
| `original/` | 70 arquivos antigos, cobertos pelo manifesto de hashes |
| `novo/src/littletec/` | Catálogo, perfis, protocolo, sessão, serviços e Qt |
| `novo/dist/` | `LittleTec.exe` atual e `_internal/`; não editar como fonte |
| `novo/tests/` | Testes puros e vetores independentes do programa original |
| `novo/tools/` | Build, lançamento, diagnóstico e smokes; scripts antigos em `historico/` |
| `novo/captures/`, `novo/analysis/` | Capturas, journals, laudos e engenharia reversa locais |
| `web/` | Desenvolvimento Web local; evidências em `.runtime/`; fora do Git desktop |
| `../littletec-web/` | Repositório Web independente, incluindo `bridge/core/littletec/` |

Os 14 módulos Python incluídos no checkout Web coincidiram com os correspondentes
do desktop na leitura de 29/10/2026. São cópias separadas, sem sincronização
automática. O Web interno e o independente diferem em documentação, lançador,
carregamento do núcleo e artefatos gerados.

## Operação atual

- Desktop Qt: leitura em worker serial, edição das três camadas, aplicação de
  teclas e giratórios com cópia, releitura e tentativa de retorno em falha.
- Web local: editor Next.js/React, API local, ponte Python Windows e relay no WSL.
  Reutiliza os serviços de configuração do Studio. Entrada ao vivo usa Raw Input
  na MI_01; configuração usa HIDAPI na MI_00.
- Pages e HTML estático: editor de perfis; não incluem a ponte USB local.
- Iluminação: envio direto, por camada ou nas três; sem recibo experimental nem
  confirmação visual obrigatória em cada aplicação.
- Perfis v1/v2, ações opacas e dados reservados preservados. Outros modelos do
  catálogo são rascunhos; USB restrito ao 12+2/variante 0 (`1189:8842`).

## Evidências e alcance

- Última execução da suíte desktop nesta retomada: **79 testes passaram** e
  **70 originais íntegros**. Verificações anteriores à presente edição documental.
- Histórico Web 0.2: 14 testes TypeScript, 28 Python e 9 Playwright registrados
  em sua documentação; não reexecutados para atualizar estes textos.
- Capturas preservam identificação, leitura, escrita/retorno dos giratórios e
  monitor ao vivo. Há 57 capturas brutas locais: 56 completas e uma tentativa
  incompleta histórica, preservada como evidência da correção.
- CI dos dois commits main consultados concluiu com sucesso; release Web e
  publicação Pages também. Pages respondeu HTTP 200 na consulta de 29/10/2026.
- A confirmação atual do usuário acrescenta uso normal de mapeamento, cores e
  aplicação em ambas as interfaces; não é um novo ensaio automatizado.

LED continua sem readback conhecido. Último envio e seleção local não são leitura
do estado interno. Não extrapolar o uso confirmado para um laudo específico de
persistência após reconexão ou para cada efeito, combinação e sistema operacional.
Esses limites não tornam a integração pendente.

## Distribuição e continuidade

O desktop atual é `dist/LittleTec.exe`, relativo a `novo/`. O build atual promove
o pacote diretamente para `dist/`. Caminhos antigos de prévia e `dist/legacy/`
nos laudos registram a organização da época; não são requisitos atuais.
`captures/qt-release-provenance.json` registra a entrega **1.0**, não o hash da 1.1.

A convergência visual desktop/Web está registrada nos READMEs. Sua execução
exige tarefa específica; não há integração básica a refazer.
Uso em [../README.md](../README.md) e documentação em [README.md](README.md).

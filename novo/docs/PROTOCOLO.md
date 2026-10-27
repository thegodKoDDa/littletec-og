# Protocolo recuperado — LittleTec 12+2

## Atualização da integração Qt — IDs armazenados de giratórios

Escrita dos slots 16..21 foi verificada no aparelho, com retorno das ações após
cada alvo. O ID da resposta FA é conteúdo armazenado e muda para o índice FD
escrito. Ex.: FD16 altera o primeiro membro que antes retornava ID18; pode então
haver respostas 16,17,16 no trio. Não tratar esse caso conhecido como perda de
registro nem mapear esses giros somente pelo ID do payload.

O leitor validado 15+3x3 usa posição do trio com validação restrita dos dois IDs
possíveis (fábrica ou escrita). Prefixos/camadas/tamanhos e duplicatas de teclas
continuam estritos. Manifesto declara stored-id-in-fixed-trios-v1. raw_layers,
JSONL, binários e hashes mantêm bytes recebidos; layers é cópia com cabeçalhos
canônicos para o codec. Dados reservados e ações não são normalizados.

Ver ENCODERS_INTEGRACAO.md. A conferência final preservou as ações e todos os
bytes além de quatro IDs na camada 1; não alegar restauração bruta integral dessa
etapa. O produto Qt escreve slots físicos 1..12/16..21 com cópia, origem, journal,
releitura e inversos. Recibos/ensaios deixaram de ser requisito de UX; comandos
FC/EF/LED arbitrários e registros opacos continuam fora desse transporte.
LED tem serviço separado e envio direto, sem afirmar readback/estado visual.

Os detalhes posteriores de bloqueio de encoder/recibos descrevem o histórico 0.4.

Estado: identificação e leitura real validadas; codificador confrontado com o
editor original; teste físico A → F24 → A aprovado pelo usuário e concluído.
Atualização LED: ciano → vermelho → ciano estáticos na camada 1 concluídos com
aprovação específica e confirmações visuais humanas; veja `LED_INVESTIGACAO.md`.
Modelo: 1189:8842, MI_00, usage page FF00/usage 1, report ID 03, relatórios de
65 bytes (ID + 64 dados). Não é firmware nem imagem de memória do microcontrolador.

## Evidências independentes

- `captures/original-record-oracle.json`: 209 observações por cliques reais no
  original; 200 controles das cinco primeiras abas, uma sequência e oito posições.
- `captures/original-delay-oracle.json`: cinco atrasos adicionais por SpinBox real.
- `tests/fixtures/original-record-vectors.json`: 206 entradas semânticas e registros
  esperados, derivados dessas capturas, com hashes de origem. Não são respostas
  inventadas pelo codificador que está sendo testado.
- `captures/*raw-configuration*`: respostas reais do aparelho. Todos os 72 registros
  foram comparados com a memória do original; após normalizar o cabeçalho de seleção,
  não houve divergência.
- Três pacotes gerados pelo `HID_write` do original, com saída bloqueada/simulada:
  LED, sequência e finalização. O codificador novo produziu bytes idênticos.

A instrumentação usa o mapa `analysis/original-function-map.json`. Cada função é
localizada unicamente no PE por correspondência com widget.o, mascarando relocações,
e o executável é validado por SHA-256 antes do ensaio. O módulo é identificado pelo
nome MINI_KEYBOARD.exe; não usar Process.mainModule durante o spawn, pois o módulo
retornado no início da instrumentação pode ser outro. Tentativas iniciais com
mapeamento inadequado e UIA Invoke foram descartadas. Invoke não reproduz o
MouseButtonRelease usado por eventFilter; somente a captura final por cliques reais
é aceita como oráculo. FD e FE foram simulados nessa captura; EF permaneceu bloqueado.

## Registro interno de 50 bytes

Offsets a partir do início do registro, não do relatório USB:

| Offset | Conteúdo recuperado | Evidência |
| --- | --- | --- |
| 0 | FD para tecla; FE para iluminação | HID_write e capturas |
| 1 | Posição de edição/gravação; B0 para LED | seleção, mapeamento e pacotes |
| 2 | Camada 1–3 | leitura e seleção |
| 3 | Tipo: 1 teclado, 2 consumidor, 3 mouse, 5 atraso, 8 LED | rotinas Set* e capturas |
| 4–5 | Atraso little-endian em ms | valores 1,255,256,1234,6000 |
| 6–8 | Sem semântica validada; preservar | leitura e reserva |
| 9 | Contagem dependente do tipo | rotinas e capturas |
| 10–49 | Dados da ação | casos do oráculo |

A resposta de leitura é `03 FA id camada ...`. `read_Hidkey_Data` copia os bytes
2..50 da resposta para offsets 1..49 do registro; FD é cabeçalho interno/de escrita.
Não enviar uma resposta 03 FA como se fosse pedido de gravação.

## Teclado

Tipo 1: até 20 pares nos 40 bytes de dados. Cada par é modificador seguido de uso
HID. O offset 9 conta etapas. Modificador isolado usa contagem 0 e máscara no
primeiro par; o botão NULL gera contagem 1 e par 00 00. As duas formas vazias são
reconhecidas e as formas originais são preservadas quando a ação não muda.

Máscaras: Ctrl 01, Shift 02, Alt 04, Win 08, Ctrl direito 10, Shift direito 20,
Alt direito 40, Win direito 80. Códigos de letras, números, navegação, numérico e
F1–F24 foram confrontados com o original. Símbolos são uso da posição US + Shift;
o resultado depende do layout do sistema. O rótulo '-' na aba estendida do original
codifica Shift+Minus (sublinhado em US); o novo usa a semântica explícita.

Exemplo: Ctrl+C, depois Shift+D → contagem 02; dados `01 06 02 07`.
O limite 20 é de armazenamento do registro recuperado, não prova de execução física
bem-sucedida de toda sequência de 20 etapas. Perfis locais antigos maiores podem
ser lidos, mas a preparação de envio recusa estouro do registro.

## Multimídia, mouse e atraso

Tipo 2: uso consumidor little-endian nos offsets 10–11. O editor original novo
marca contagem 2; registros reais de fábrica têm contagem 1. O novo preserva a
contagem original quando a ação não mudou. Mapeamento dos 21 controles em
protocol.MEDIA_CODES, todos confrontados com o editor.

Tipo 3: contagem 1. Offset 10 contém modificadores; offset 11 contém botões
(01 esquerdo, 02 direito, 04 meio); offset 14 é roda (01 acima, FF abaixo).
As 11 combinações foram confrontadas. Movimentos X/Y e padrões não compreendidos
não são reduzidos a ações conhecidas: ficam opacos.

Tipo 5: atraso de 0–6000 ms em 4–5, contagem 0. Não supor que um atraso inserido
em outro tipo seja equivalente; o decodificador preserva formas não compreendidas.

## Encoders: leitura e escrita não têm a mesma numeração no fluxo original

Os slots de edição observados são 16/esquerda,17/clique,18/direita para encoder 1;
19,20,21 para encoder 2. Porém o original lê cada trio na ordem 18,17,16, depois
21,20,19 e 24,23,22, e copia esses dados sequencialmente para os slots internos.
Ao selecionar uma posição, on_changeButtonGroup reescreve o cabeçalho com o slot
de edição. Assim, o registro recebido com ID 18 alimenta o slot editável 16.

O decodificador usa uma transformação explícita por trio (16↔18, 19↔21, 22↔24),
não a ordem ocasional de chegada. As respostas brutas são preservadas intactas.
A transformação foi confrontada com os 72 registros na memória do original e
com a seleção das posições. A leitura atual mostra encoder 1 como volume−,
silenciar, volume+; encoder 2 como 4,5,6.

**A gravação de encoders não foi testada no aparelho.** Ela permanece recusada no
transporte, mesmo com o formato do editor recuperado, para não confundir equivalência
com o programa antigo com validação física da numeração de escrita.

## Iluminação

Registro `FE B0 camada 08`, contagem 1. Offset 11 contém a cor no nibble alto
(1 vermelho,2 laranja,3 amarelo,4 verde,5 ciano,6 azul,7 roxo) e modo 0–5 no baixo.
Os 13 controles e um pacote nativo foram confrontados. Isso recupera a codificação,
não o estado atual do aparelho: o fluxo FA observado não retorna esse registro.

Perfis lidos pelo USB usam `{mode: null, color: null}`. A interface mostra estado
não lido e não inventa uma cor. Na versão 0.4, a seleção pode partir da última
referência visual confirmada, explicitamente identificada como tal na interface;
a cópia bruta e o decodificador continuam sem valor LED inventado.

O usuário autorizou posteriormente estabelecer ciano estático sem readback do
LED anterior na camada 1, testar vermelho e voltar ao ciano. Foram enviados FE B0
01 (tipo 08, contagem 01, código 51 ou 11) + finalização FD FE FF. Cada pacote
tem 65 bytes, padding zero, e foi confrontado com HID_write nativo simulado.
As três aparências foram confirmadas pelo usuário; os 72 relatórios completos
de teclas/encoders coincidiram antes/depois. Isso valida retorno à referência
estabelecida, sem comprovar recuperação do estado LED interno anterior desconhecido.

Envio normal LED é separado de FD de teclas e exige recibo específico por
identidade/caminho/camada. Antes/depois são confirmados visualmente; falha tenta
enviar o pacote inverso. Interrupção/retorno não confirmado invalida a referência.
Sem detecção automática de mudanças externas: o usuário deve cancelar se a
referência exibida não corresponder ao teclado. Ainda não há persistência após
reconexão validada; efeitos individuais fora do estático seguem sem ensaio físico.

## Pacotes de gravação e retorno

HID_write: `03` + registro de 50 bytes + 14 zeros. Finalização:
`03 FD FE FF` + 61 zeros; espera original de 200 ms. O codificador novo foi
confrontado com o pacote nativo bloqueado para cada parte conhecida.

Um plano de alteração contém bytes antes/depois e o pacote inverso por posição.
Campos desconhecidos e padrões não interpretados são preservados como ação raw,
com 50 bytes em hexadecimal. Não é permitido mover ou modificar silenciosamente
a ação opaca; o transporte recusa sua substituição antes de compreender os campos.

## Ensaio físico aprovado e restauração

O usuário autorizou explicitamente A → F24 → A na tecla 1/camada 1. A ferramenta:

1. Leu e guardou uma cópia bruta recente com hashes.
2. Reenviou o A atual + finalização, e exigiu igualdade dos 72 relatórios.
3. Só após esse teste sem alteração semântica, enviou F24 para a mesma posição.
4. Leu o aparelho e confirmou que exclusivamente aquela posição mudou.
5. Restaurou o pacote original de A em finally e comparou todos os 72 relatórios.

Resultado `captures/write-restore-trial.json`: noop_verified, change_verified,
restoration_verified e complete todos true. Sem erros. Recibo local em
`%LOCALAPPDATA%\LittleTec\write-validation.json`, associado ao caminho HID e identidade.
O mesmo ensaio aprovado foi repetido pela integração da interface e também terminou
com os 72 relatórios idênticos ao início. O estado final da tecla é A.

A validação física cobre esse ensaio de teclado comum. Não foram testados um
pressionamento físico de F24, sua persistência após reconectar, escrita em encoder
ou LED, nem todos os efeitos de cada código multimídia/mouse no sistema operacional.
Não chamar a cópia dos 72 relatórios de imagem completa de memória/firmware.

## Fluxo de aplicação do Studio

- Ler teclado: identifica, lê, guarda cópia bruta e decodifica para o editor.
- Editar e revisar: mostra antes/depois e permite exportar o plano.
- Aplicar teclas: exige o recibo de restauração deste dispositivo; uma nova leitura
  com cópia deve coincidir com a origem carregada, evitando sobrescrever mudanças
  externas ou uma cópia antiga. Envia apenas posições 1–12 e camadas 1–3, nos tipos
  codificados conhecidos, com tamanho completo e finalização por camada.
- Relê o aparelho: compara semanticamente as ações alteradas e byte a byte os
  registros não alterados. Em falha, tenta enviar os pacotes inversos e comprovar
  o retorno integral. Se o retorno falhar (por exemplo desconexão), invalida o
  recibo e informa a cópia anterior; não promete restauração sem acesso ao aparelho.

FD é o único tipo de escrita aceito no transporte de teclas e seu índice é limitado a teclas comuns.
Atualização/flash, FE de LED, FC, encoders e pedidos arbitrários não são aceitos
pelo transporte de teclas. `lighting_service` admite exclusivamente LED FE B0
canônico + finalização fixa, conforme os limites e validação visual acima.
Consultas FB/FA, escrita FD e LED têm funções e listas separadas.
O usuário só inicia aplicação pelo botão da revisão; abrir o aplicativo faz apenas
enumeração de presença, sem carregar ou gravar configuração automaticamente.

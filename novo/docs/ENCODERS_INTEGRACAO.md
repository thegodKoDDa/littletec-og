# Endereçamento de giratórios na integração Qt

O pedido atual exige concluir a escrita dos giratórios, sem repetir pesquisas ou
ensaios de cores. A questão específica pendente é a relação entre slot de escrita
FD e ID de resposta FA. A leitura já normaliza trios 16↔18 e 19↔21 para reproduzir
o editor original; isso não prova que o hardware devolva o mesmo índice gravado.

`tools/resolve_encoder_addressing_windows.py` prepara uma cópia recente completa.
Origem dos envios: HID_write original, documentado em PROTOCOLO.md: 03 + registro
FD de 50 bytes + 14 zeros; finalização 03 FD FE FF + 61 zeros, espera 200 ms.
O marcador F23 foi confrontado com os vetores nativos. Sem FC/EF/LED.

Por posição 16..21 da camada 1, o plano salva os 65 bytes temporários e todos os
possíveis inversos antes de comunicar. F23 temporário usa tipo 1, count 1, mod 00,
uso 72. Após releitura, o único ID realmente alterado determina qual registro bruto
anterior reenviar ao MESMO slot de escrita. A restauração é conferida nos 72
relatórios completos antes da posição seguinte. Nenhum giro físico é automatizado;
isso valida endereçamento/retorno, não eventos no sistema ou persistência.

O script requer --execute para operar; não participa de testes unitários/smoke/build.
Evidência real, quando concluída: captures/encoder-addressing-<data>.json.

## Resultado real e correção

A primeira escrita FD16 chegou ao primeiro slot do trio (o volume− da cópia), mas
substituiu seu ID armazenado 18 por 16. O firmware repete o ID armazenado na
resposta FA. Assim, ficaram IDs 16,17,16 no trio: o leitor estrito recusou a
resposta e a primeira versão do script não executou retorno com target ausente.
O retorno foi então enviado explicitamente ao slot 16 com o corpo volume− da
cópia. Comparação em `captures/encoder-first-restoration.json`: só o byte de ID
mudou; ação, reservados e padding foram restaurados.

O leitor agora aceita no fluxo validado de cada trio somente o ID de fábrica
invertido ou o ID de escrita daquele slot. Duplicatas de teclas, prefixo, camada,
comprimentos, timeout e IDs fora do par continuam recusados. Essa política é
ativada depois da identificação 12+2/0. `normalize_encoder_headers` produz uma
cópia para interpretação; os arquivos binários, JSONL, hashes e `raw_layers`
preservam os bytes efetivamente recebidos. `layers` é a representação canônica
para o codec existente quando a política está declarada no manifesto.

A verificação restante dos slots 17..21 passou com retorno das ações. Evidências:
`captures/encoder-addressing-20261027T181426472163Z.json` (primeira tentativa e
comando de retorno) e `captures/encoder-addressing-20261027T181858668100Z.json`
(cinco slots concluídos). Não repetir esses ensaios no uso normal.

Comparação final independente em `captures/encoder-integration-comparison.json`:
os 72 relatórios têm os mesmos corpos/reservados/padding; **quatro bytes de ID
armazenado da camada 1** passaram da forma de fábrica para os slots de escrita.
Não houve igualdade bruta integral com a origem, e isso não deve ser relatado
como se houvesse. As ações dos giratórios e teclas foram restauradas; não ficou
F23 temporário. Vetores reais mínimos versionáveis em
`tests/fixtures/encoder-stored-id-vectors.json`.

Mapeamento de produto: slots de edição/escrita 16,17,18 e 19,20,21 correspondem
às posições sequenciais dos dois trios no fluxo de leitura. IDs do payload FA
podem mudar após escrever e não podem ser a única identidade desses slots.
Não foi testado o giro/pressionamento físico nem persistência após reconexão.

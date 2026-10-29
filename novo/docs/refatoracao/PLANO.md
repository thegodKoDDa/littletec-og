# Continuidade após a integração — 29/10/2026

**A integração desktop e Web está concluída e funcionando**, incluindo
mapeamento, cores e aplicação, conforme o usuário. Este roteiro substitui o
plano antigo de concluir uma prévia Qt. Consulte [estado atual](../ESTADO_ATUAL.md).

## Marcos já entregues

| Etapa | Resultado |
| --- | --- |
| Separar edição da GUI | `EditorSession`, domínio e perfis preservados |
| Integrar Qt ao dispositivo | Worker serial e `ConfigurationService` |
| Aplicar LED diretamente | Fluxo sem recibos/ensaios no uso cotidiano |
| Resolver escrita dos knobs | Slots 16–21 e tratamento de IDs armazenados |
| Completar configuração | Catálogo, perfis, revisão, histórico e cópias |
| Distribuir desktop | Studio 1.1.0 publicado, executável integrado |
| Implementar Web | Web 0.2.0, ponte Windows/relay e entrada ao vivo |
| Publicar Web | Release e Pages disponíveis |

O plano original também propunha uma divisão futura de pastas de infraestrutura;
a estrutura efetiva está em [ARQUITETURA.md](ARQUITETURA.md). Não considerar toda
sugestão organizacional antiga uma integração funcional ainda por fazer.

## Como continuar

1. Partir do [estado vigente](../ESTADO_ATUAL.md) e da tarefa solicitada pelo usuário.
2. Identificar a cópia de trabalho: desktop, Web interno ou repositório Web independente.
3. Preservar protocolo, perfis, campos desconhecidos, capturas e produto funcional.
4. Validar somente o que a mudança justificar. Testes simulados e builds não
   devem iniciar testes físicos automaticamente.
5. Atualizar documentos correntes quando o comportamento mudar; manter laudos
   históricos com sua data e alcance.

A direção futura registrada é convergir o visual desktop para a referência Web.
Não há decisão de implementação adicional neste documento nem autorização
implícita para migração, commits, releases ou novos ensaios físicos.

## Verificações de referência

Desktop: testes puros em `novo/tests/`, 206 vetores nativos e verificação dos
originais. Web: testes TypeScript, Python e navegador com serviços simulados.
Procedimentos em [RETOMADA_WSL.md](../RETOMADA_WSL.md) e nos READMEs.
Não repetir A/F24, ciclo de cores ou endereçamento de giros por rotina.

Os seis marcos e comandos anteriores foram preservados integralmente em
`../historico/PLANO_20261027.md` (arquivo local, fora do Git).

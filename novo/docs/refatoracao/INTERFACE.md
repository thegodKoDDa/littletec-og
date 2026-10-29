# Interface e fluxos atuais — 29/10/2026

**Desktop 1.1.0 e Web 0.2.0 funcionam para configurar o teclado**, conforme
confirmação do usuário. Uso cotidiano em [guia desktop](../../README.md) e no
[README Web](https://github.com/thegodKoDDa/littletec-web). Estado e versões em
[ESTADO_ATUAL.md](../ESTADO_ATUAL.md).

## Organização implementada

| Área | Desktop Qt | Web |
| --- | --- | --- |
| Mapeamento | Grade de teclas, cartões dos dois knobs, catálogo e editor | Placa interativa, editor contextual e ferramentas de edição |
| Giratórios | Esquerda, clique e direita; presets, inversão, troca e replicação | Controles no mapeamento e página Giratórios dedicada |
| Iluminação | Sete cores, seis modos, envio por camada ou nas três; opção de envio automático | Prévia local, seleção e envio por camada ou nas três |
| Perfis | Novo, abrir, salvar/salvar como, modelos e cópias | Biblioteca do navegador, importar/exportar JSON, modelos e cópias |
| Diagnóstico | Área secundária e exportação | Página de conexão e exportação |
| Entrada ao vivo | Não implementada na interface Qt atual | Raw Input, atividade, destaques e dials animados |

Desktop usa tema azul/grafite e opção clara. Web usa identidade verde/grafite,
fontes DM Sans/Manrope e layouts responsivos. Os READMEs registram o Web como
referência para futura convergência visual; isso não descreve uma migração já feita.

## Fluxos

- **Conectar:** desktop lê em segundo plano ao abrir; Web conecta pelo botão e
  ponte local. Leitura não deve substituir silenciosamente edições em andamento.
- **Editar:** selecionar tecla ou alvo do knob; capturar combinação pelo teclado
  principal ou escolher no catálogo. Presets e templates alteram o rascunho.
- **Sequências:** adicionar, remover, reordenar e editar etapas. Até 20 pares no
  registro de hardware; atraso é uma ação própria, não pausa arbitrária entre eventos.
- **Aplicar mapeamento:** revisão contextual, cópia recente, envio e conferência
  por releitura. Teclas e giratórios já têm escrita integrada.
- **Iluminação:** envio direto, sem repetir ensaios ou exigir recibos visuais.
  Seleção local e último envio não são leitura do LED interno.
- **Limpar:** escopo de posição/camada/tudo, edição local reversível até aplicar.
- **Salvar:** arquivo ou biblioteca local não enviam automaticamente o mapeamento.

## Entrada ao vivo Web

Eventos vêm da MI_01 e são associados ao snapshot do aparelho. Comandos iguais
em posições distintas são ambíguos. O dispositivo não informa camada ativa ou
ângulo absoluto nesse fluxo; a animação representa os comandos identificados.
O monitor é passivo e não bloqueia ações no Windows.

## Regras para manutenção

Preservar catálogo completo, perfis v1/v2, campos opacos, histórico e cópias.
Manter foco, nomes acessíveis, estados legíveis, rolagem, tema claro/escuro e
redimensionamento. Não construir bytes em QML/React, não adicionar FC/EF ou
firmware ao uso comum e não apresentar modelos de rascunho como suporte USB.

O inventário está em [FUNCIONALIDADES.json](FUNCIONALIDADES.json).
A proposta original está preservada em
`../historico/INTERFACE_20261027.md` (arquivo local, fora do Git).

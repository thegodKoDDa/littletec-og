# Estado do arquivo OG

Por decisão do usuário em 29/10/2026, o desenvolvimento aqui está encerrado.
O projeto ativo é `../littletec-studio`, repositório `thegodKoDDa/littletecstudio`.
Preservar o Qt 1.1.0, executável, originais, fontes, capturas e histórico.
A cópia Web foi transferida para o histórico local do Studio. Não recriar `web/`.
As orientações técnicas abaixo documentam o funcionamento preservado e não
são autorização para reiniciar desenvolvimento ou testes físicos neste arquivo.

# LittleTec OG — arquivo preservado

Atualizado em **29/10/2026**. Escopo: todo este diretório.

## Estado confirmado pelo usuário

O **Studio desktop 1.1.0 e o Web 0.2.0 estão funcionando em uso real**:
mapeamento, troca de cores e aplicação das mudanças no teclado. O usuário
destacou especialmente o bom funcionamento do Web. Essa confirmação prevalece
sobre pendências de integração descritas em documentos históricos.

- Desktop: Python + PySide6/Qt Quick/QML + HIDAPI, Windows x64.
- Web: Next.js/React/TypeScript; USB pela ponte Python Windows, com relay no WSL.
- Pages e HTML estático oferecem o editor; o uso USB confirmado é o Web local
  com a ponte. Não confundir as formas de execução.
- Escrita dos giratórios resolvida e integrada. Não retomar essa tarefa como pendente.
- Versões publicadas: desktop `v1.1.0` e Web `v0.2.0`. Git/GitHub já configurados.
- Convergência visual do desktop para a referência Web é uma direção registrada;
  não é uma migração já executada nem autorização para iniciá-la nesta tarefa.

## Onde começar

Leia [RETOMAR.md](RETOMAR.md), [estado atual](novo/docs/ESTADO_ATUAL.md) e
[índice da documentação](novo/docs/README.md). Para trabalho técnico, consulte
[arquitetura](novo/docs/refatoracao/ARQUITETURA.md),
[protocolo](novo/docs/PROTOCOLO.md) e o inventário de funcionalidades.

- `novo/`: código e distribuição do desktop; `novo/dist/LittleTec.exe` é o atual.
- `web/`: cópia local de desenvolvimento Web, com evidências em `.runtime/`.
- `../littletec-web/`: checkout do repositório Web independente, com núcleo Python
  em `bridge/core/littletec/`. Não presumir sincronização automática entre cópias.
- `original/`: 70 arquivos antigos preservados. Não alterar seus binários.

## Preservação e comunicação

- Preservar protocolo, perfis v1/v2, ações opacas, reservados e limites dos registros.
- Capturas e vetores locais prevalecem sobre bytes externos com o mesmo VID/PID.
- `analysis/`, `captures/`, `.devtools/`, `.runtime/` e ambientes são material local.
  Não apagar evidências ao reorganizar. Não publicar tokens ou dados privados.
- LED não tem readback conhecido. Identificar seleção local e último envio sem
  alegar leitura do estado interno. Isso não impede a troca de cores funcional.
- A confirmação de uso não é laudo específico de persistência após reconexão,
  de cada efeito ou de cada combinação. Não inventar esses resultados.
- Recibos e ensaios da versão 0.4 são históricos; não reintroduzir essas exigências
  no uso cotidiano. Não repetir ensaios de cores, A/F24 ou slots por rotina.
- Não confundir aplicativo com firmware. FC/EF, flash e troca de driver ficam
  fora do fluxo normal de configuração.

## Desenvolvimento

- Nenhum protocolo USB em QML/React; nenhum componente GUI no domínio.
- Desktop serializa I/O em worker fora da thread visual. Web serializa operações
  na ponte e usa revisão de snapshot entre abas.
- WSL mantém o transporte Windows funcional, sem exigir USB direto no Linux.
- Testes físicos são opt-in e separados de unitários, smoke visual e build.
- Testes puros desktop: `cd novo` e `python3 -m unittest discover -s tests -q`.
- Ambiente Windows: `novo/.venv-qt-windows`; dependências em `novo/requirements/`.
  Entrada normal: `tools/studio_qt.py`; build: `tools/build_qt_windows.py`.
- Não criar commits, remotos, releases ou publicações sem pedido específico.
- Conversar e documentar em português. Documentos históricos e laudos datados
  descrevem suas etapas, não pendências atuais automáticas.

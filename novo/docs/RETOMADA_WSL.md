# Retomada pelo WSL — 29/10/2026

Referência: [estado atual](ESTADO_ATUAL.md). **Desktop e Web local estão
funcionais para mapeamento, cores e aplicação**, conforme o usuário.

## Ambiente e execução

WSL é usado para editar e executar testes puros. Comunicação com o teclado
continua pelo Windows; não precisa encaminhar USB ao WSL nem trocar drivers.

A partir de `novo/`, no ambiente existente:

```bash
# Domínio e integridade, sem dispositivo físico:
python3 -m unittest discover -s tests -q
python3 tools/littletec.py verify

# Aplicação normal Windows; faz leitura automática ao abrir:
.venv-qt-windows/Scripts/python.exe tools/studio_qt.py

# Abrir sem conexão automática (os botões USB continuam reais):
.venv-qt-windows/Scripts/python.exe tools/studio_qt.py --offline

# Build Windows, somente quando a tarefa exigir:
.venv-qt-windows/Scripts/python.exe tools/build_qt_windows.py
```

Dependências em `requirements/`; empacotamento atual em `tools/build_qt_windows.py`,
com entrada `src/desktop_qt.py` e saída em `dist/`. Manter `_internal/` ao lado.
`tools/preview_qt.py` é compatibilidade para abrir sem conexão automática;
não representa um produto separado sem integração.

## Web

A cópia `../web/`, relativa a `novo/`, usa o ambiente Windows do desktop e relay
para o WSL/NAT. O checkout independente fica em `../../littletec-web/` e tem
README próprio. Não presumir sincronização automática nem configuração de
ambiente idêntica entre os dois diretórios.

`npm run dev` inicia interface e ponte na pasta Web; `npm run dev:ui` inicia
somente a interface. Não executar leitura, escrita ou monitoramento físico
como parte automática de uma revisão documental ou de testes simulados.

## Preservação

Não repetir A/F24, ensaios de cores ou slots dos giros por rotina. LED permanece
sem readback; último envio não é leitura do estado interno. Preservar dados
brutos e normalizar cabeçalhos de encoder apenas na cópia de interpretação.

A retomada anterior, incluindo a preparação da prévia e problemas já resolvidos
de build, foi preservada em
`historico/RETOMADA_WSL_ATE_20261028.md` (arquivo local, fora do Git).

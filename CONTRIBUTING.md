# Contribuir

Use as [issues](https://github.com/thegodKoDDa/littletec/issues) para relatar problemas ou propor melhorias. Antes de enviar uma alteração ampla no protocolo ou na interface, descreva o comportamento observado e o modelo do teclado.

## Preparar o ambiente

Siga as instruções no [README](README.md). O código-fonte ativo fica em `novo/`:

- `novo/src/littletec/protocol.py`: codificação e decodificação pura dos registros de 50 bytes e pacotes HID de 65 bytes (`1189:8842`).
- `novo/src/littletec/catalog.py`: catálogo de teclas, multimídia, mouse, presets de knobs, templates de camada e reconhecimento do teclado físico.
- `novo/src/littletec/configuration_service.py`: leitura, verificação, cópia de segurança e envio de teclas, knobs e iluminação LED.
- `novo/src/littletec/ui_qt/`: controlador Qt (`controller.py`), worker USB em thread separada (`device_worker.py`) e interface QML (`qml/`).

## Validar uma alteração

Na pasta `novo/`:

```bash
python3 -m unittest discover -s tests -v
```

Os testes unitários rodam de forma isolada sem acessar dispositivos USB físicos. Alterações no protocolo devem manter compatibilidade com todos os vetores reais em `novo/tests/fixtures/`.

## Enviar uma proposta

Abra um pull request descrevendo o problema, a solução adotada e os testes executados. Atualize o [CHANGELOG.md](CHANGELOG.md) quando houver mudanças visíveis ao usuário.

Não inclua binários compilados (`dist/`, `*.exe`), capturas locais (`captures/`), ambientes virtuais (`.venv*`) ou dados pessoais no Git.

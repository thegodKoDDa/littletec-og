"""Entry point fora de tools/: evita o módulo homônimo littletec.py no build."""
from littletec.ui_qt.launcher import main

if __name__ == '__main__':
    raise SystemExit(main())

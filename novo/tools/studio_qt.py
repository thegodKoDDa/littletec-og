"""Inicia a versão Qt integrada; opções em --help."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.ui_qt.launcher import main

if __name__ == '__main__':
    raise SystemExit(main())

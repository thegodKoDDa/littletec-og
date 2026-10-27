"""Compatibilidade: abre o Studio Qt sem conexão automática.
Os botões de leitura/aplicação são reais. Use tools/studio_qt.py no uso normal.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from littletec.ui_qt.launcher import main

if __name__ == '__main__':
    sys.argv.insert(1, '--offline')
    raise SystemExit(main())

"""Catálogo de teclas, atalhos prontos, mídia, captura de teclado e tonalidades."""
import math

KEYS = tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') + tuple(f'F{i}' for i in range(1, 25)) + (
    'Escape', 'Tab', 'CapsLock', 'Enter', 'Space', 'Backspace', 'Delete', 'Insert',
    'Home', 'End', 'PageUp', 'PageDown', 'PrintScreen', 'ScrollLock', 'Pause',
    'Up', 'Down', 'Left', 'Right', 'Menu', 'NumLock', 'IntlBackslash',
    'Grave', 'Minus', 'Equal', 'BracketLeft', 'BracketRight', 'Backslash',
    'Semicolon', 'Quote', 'Comma', 'Period', 'Slash',
    'NumEnter', 'NumAdd', 'NumSubtract', 'NumMultiply', 'NumDivide', 'NumDecimal',
    *tuple(f'Num{i}' for i in range(10)))
MODIFIERS = ('Ctrl', 'Shift', 'Alt', 'Win', 'RightCtrl', 'RightShift', 'RightAlt', 'RightWin')
KEY_LABELS = {'Escape': 'Esc', 'CapsLock': 'Caps Lock', 'Space': 'Espaço', 'Backspace': 'Backspace',
              'Delete': 'Del', 'Insert': 'Ins', 'PageUp': 'PgUp', 'PageDown': 'PgDn',
              'PrintScreen': 'PrtSc', 'ScrollLock': 'Scroll', 'Pause': 'Pause',
              'Up': '↑', 'Down': '↓', 'Left': '←', 'Right': '→', 'Menu': 'Menu',
              'Grave': '` ~', 'Minus': '- _', 'Equal': '= +', 'BracketLeft': '[ {',
              'BracketRight': '] }', 'Backslash': '\\ |', 'Semicolon': '; :',
              'Quote': "' \"", 'Comma': ', <', 'Period': '. >', 'Slash': '/ ?',
              'IntlBackslash': '< >', 'NumEnter': 'Num Enter', 'NumAdd': 'Num +',
              'NumSubtract': 'Num −', 'NumMultiply': 'Num ×', 'NumDivide': 'Num ÷',
              'NumDecimal': 'Num .'}
MOD_LABELS = {'RightCtrl': 'Ctrl direito', 'RightShift': 'Shift direito',
              'RightAlt': 'Alt direito', 'RightWin': 'Win direito'}
MEDIA = {
    'play_pause': 'Reproduzir / pausar', 'stop': 'Parar', 'previous': 'Faixa anterior',
    'next': 'Próxima faixa', 'volume_up': 'Volume +', 'volume_down': 'Volume −',
    'mute': 'Silenciar', 'brightness_up': 'Brilho da tela +', 'brightness_down': 'Brilho da tela −',
    'computer': 'Meu computador', 'calculator': 'Calculadora', 'media_player': 'Multimídia',
    'browser_home': 'Página inicial', 'email': 'E-mail', 'bass_up': 'Graves +',
    'bass_down': 'Graves −', 'treble_up': 'Agudos +', 'treble_down': 'Agudos −',
    'browser_refresh': 'Atualizar página', 'browser_forward': 'Avançar página',
    'browser_back': 'Voltar página'}
MOUSE = {'left': 'Clique esquerdo', 'middle': 'Clique do meio', 'right': 'Clique direito',
         'wheel_up': 'Roda para cima', 'wheel_down': 'Roda para baixo'}
COLORS = {'red': ('Vermelho', '#ef4444'), 'orange': ('Laranja', '#f59e0b'),
          'yellow': ('Amarelo', '#e1e100'), 'green': ('Verde', '#80c448'),
          'cyan': ('Ciano', '#22d3ee'), 'blue': ('Azul', '#3b82f6'), 'purple': ('Roxo', '#a855f7')}

LED_MODES = (
    {'id': 0, 'name': 'Modo 0 · Desligado (Off)'},
    {'id': 1, 'name': 'Modo 1 · Luz Fixa (Backlight)'},
    {'id': 2, 'name': 'Modo 2 · Respiração / Pulso'},
    {'id': 3, 'name': 'Modo 3 · Ciclo de Cores'},
    {'id': 4, 'name': 'Modo 4 · Reativo (Onda / Shock)'},
    {'id': 5, 'name': 'Modo 5 · Acender ao Pressionar'},
)

COLOR_SHADES = (
    # Vermelho (Hardware 1 · red)
    {'name': 'Vermelho Vivo', 'hex': '#ef4444', 'hw': 'red'},
    {'name': 'Rubi Profundo', 'hex': '#be123c', 'hw': 'red'},
    {'name': 'Coral Neon', 'hex': '#fb7185', 'hw': 'red'},
    {'name': 'Rosa Choque', 'hex': '#ec4899', 'hw': 'red'},
    # Laranja (Hardware 2 · orange)
    {'name': 'Salmão Quente', 'hex': '#f97316', 'hw': 'orange'},
    {'name': 'Laranja Intenso', 'hex': '#f59e0b', 'hw': 'orange'},
    {'name': 'Âmbar Dourado', 'hex': '#d97706', 'hw': 'orange'},
    {'name': 'Tangerina', 'hex': '#ea580c', 'hw': 'orange'},
    # Amarelo (Hardware 3 · yellow)
    {'name': 'Ouro Solar', 'hex': '#eab308', 'hw': 'yellow'},
    {'name': 'Amarelo Limão', 'hex': '#facc15', 'hw': 'yellow'},
    {'name': 'Amarelo Puro', 'hex': '#e1e100', 'hw': 'yellow'},
    {'name': 'Amarelo Canário', 'hex': '#fde047', 'hw': 'yellow'},
    # Verde (Hardware 4 · green)
    {'name': 'Lima Elétrico', 'hex': '#a3e635', 'hw': 'green'},
    {'name': 'Verde Folha', 'hex': '#80c448', 'hw': 'green'},
    {'name': 'Verde Puro', 'hex': '#22c55e', 'hw': 'green'},
    {'name': 'Esmeralda', 'hex': '#10b981', 'hw': 'green'},
    # Ciano (Hardware 5 · cyan)
    {'name': 'Verde Água', 'hex': '#2dd4bf', 'hw': 'cyan'},
    {'name': 'Turquesa', 'hex': '#14b8a6', 'hw': 'cyan'},
    {'name': 'Ciano Clássico', 'hex': '#22d3ee', 'hw': 'cyan'},
    {'name': 'Azul Gelo', 'hex': '#67e8f9', 'hw': 'cyan'},
    # Azul (Hardware 6 · blue)
    {'name': 'Azul Celeste', 'hex': '#38bdf8', 'hw': 'blue'},
    {'name': 'Azul Oceano', 'hex': '#0284c7', 'hw': 'blue'},
    {'name': 'Azul Royal', 'hex': '#3b82f6', 'hw': 'blue'},
    {'name': 'Azul Cobalto', 'hex': '#1d4ed8', 'hw': 'blue'},
    # Roxo (Hardware 7 · purple)
    {'name': 'Índigo', 'hex': '#6366f1', 'hw': 'purple'},
    {'name': 'Violeta', 'hex': '#8b5cf6', 'hw': 'purple'},
    {'name': 'Roxo Neon', 'hex': '#a855f7', 'hw': 'purple'},
    {'name': 'Magenta', 'hex': '#d946ef', 'hw': 'purple'},
)

SHORTCUT_PRESETS = (
    # Edição e área de transferência
    ('Copiar (Ctrl+C)', [{'key': 'C', 'modifiers': ['Ctrl']}]),
    ('Colar (Ctrl+V)', [{'key': 'V', 'modifiers': ['Ctrl']}]),
    ('Recortar (Ctrl+X)', [{'key': 'X', 'modifiers': ['Ctrl']}]),
    ('Desfazer (Ctrl+Z)', [{'key': 'Z', 'modifiers': ['Ctrl']}]),
    ('Refazer (Ctrl+Y)', [{'key': 'Y', 'modifiers': ['Ctrl']}]),
    ('Selecionar tudo (Ctrl+A)', [{'key': 'A', 'modifiers': ['Ctrl']}]),
    ('Salvar (Ctrl+S)', [{'key': 'S', 'modifiers': ['Ctrl']}]),
    ('Buscar / Localizar (Ctrl+F)', [{'key': 'F', 'modifiers': ['Ctrl']}]),
    ('Imprimir (Ctrl+P)', [{'key': 'P', 'modifiers': ['Ctrl']}]),
    ('Novo (Ctrl+N)', [{'key': 'N', 'modifiers': ['Ctrl']}]),
    ('Duplicar (Ctrl+D)', [{'key': 'D', 'modifiers': ['Ctrl']}]),
    ('Copiar e Colar (Ctrl+C → Ctrl+V)', [{'key': 'C', 'modifiers': ['Ctrl']}, {'key': 'V', 'modifiers': ['Ctrl']}]),
    ('Selecionar Tudo e Copiar (Ctrl+A → Ctrl+C)', [{'key': 'A', 'modifiers': ['Ctrl']}, {'key': 'C', 'modifiers': ['Ctrl']}]),
    ('Selecionar Tudo e Apagar (Ctrl+A → Del)', [{'key': 'A', 'modifiers': ['Ctrl']}, {'key': 'Delete', 'modifiers': []}]),
    # Sistema e Janelas
    ('Alternar janela (Alt+Tab)', [{'key': 'Tab', 'modifiers': ['Alt']}]),
    ('Fechar janela (Alt+F4)', [{'key': 'F4', 'modifiers': ['Alt']}]),
    ('Mostrar área de trabalho (Win+D)', [{'key': 'D', 'modifiers': ['Win']}]),
    ('Bloquear PC (Win+L)', [{'key': 'L', 'modifiers': ['Win']}]),
    ('Explorador de Arquivos (Win+E)', [{'key': 'E', 'modifiers': ['Win']}]),
    ('Recorte de tela / Print (Win+Shift+S)', [{'key': 'S', 'modifiers': ['Shift', 'Win']}]),
    ('Histórico da área de transferência (Win+V)', [{'key': 'V', 'modifiers': ['Win']}]),
    ('Painel de Emojis (Win+.)', [{'key': 'Period', 'modifiers': ['Win']}]),
    ('Gerenciador de Tarefas (Ctrl+Shift+Esc)', [{'key': 'Escape', 'modifiers': ['Ctrl', 'Shift']}]),
    ('Executar comando (Win+R)', [{'key': 'R', 'modifiers': ['Win']}]),
    ('Configurações do Windows (Win+I)', [{'key': 'I', 'modifiers': ['Win']}]),
    ('Visão de Tarefas (Win+Tab)', [{'key': 'Tab', 'modifiers': ['Win']}]),
    ('Minimizar tudo (Win+M)', [{'key': 'M', 'modifiers': ['Win']}]),
    ('Desktop virtual anterior (Ctrl+Win+←)', [{'key': 'Left', 'modifiers': ['Ctrl', 'Win']}]),
    ('Próximo desktop virtual (Ctrl+Win+→)', [{'key': 'Right', 'modifiers': ['Ctrl', 'Win']}]),
    # Navegador e Abas
    ('Nova aba (Ctrl+T)', [{'key': 'T', 'modifiers': ['Ctrl']}]),
    ('Fechar aba (Ctrl+W)', [{'key': 'W', 'modifiers': ['Ctrl']}]),
    ('Reabrir aba fechada (Ctrl+Shift+T)', [{'key': 'T', 'modifiers': ['Ctrl', 'Shift']}]),
    ('Próxima aba (Ctrl+Tab)', [{'key': 'Tab', 'modifiers': ['Ctrl']}]),
    ('Aba anterior (Ctrl+Shift+Tab)', [{'key': 'Tab', 'modifiers': ['Ctrl', 'Shift']}]),
    ('Janela anônima (Ctrl+Shift+N)', [{'key': 'N', 'modifiers': ['Ctrl', 'Shift']}]),
    ('Atualizar sem cache (Ctrl+F5)', [{'key': 'F5', 'modifiers': ['Ctrl']}]),
    ('Zoom + (Ctrl+=)', [{'key': 'Equal', 'modifiers': ['Ctrl']}]),
    ('Zoom − (Ctrl+-)', [{'key': 'Minus', 'modifiers': ['Ctrl']}]),
    ('Zoom 100% (Ctrl+0)', [{'key': '0', 'modifiers': ['Ctrl']}]),
    # Comunicação, Streaming e Jogos
    ('Mudo Discord / Teams (Ctrl+Shift+M)', [{'key': 'M', 'modifiers': ['Ctrl', 'Shift']}]),
    ('Ensurdecer Discord (Ctrl+Shift+D)', [{'key': 'D', 'modifiers': ['Ctrl', 'Shift']}]),
    ('Gravar clipe 30s (Win+Alt+G)', [{'key': 'G', 'modifiers': ['Alt', 'Win']}]),
    ('Gravar tela (Win+Alt+R)', [{'key': 'R', 'modifiers': ['Alt', 'Win']}]),
    ('Mudo microfone Windows (Win+Alt+K)', [{'key': 'K', 'modifiers': ['Alt', 'Win']}]),
)

QUICK_ACTIONS = (
    {'title': '⏮ Faixa anterior', 'action': {'type': 'media', 'command': 'previous'}},
    {'title': '⏯ Reproduzir / pausar', 'action': {'type': 'media', 'command': 'play_pause'}},
    {'title': '⏭ Próxima faixa', 'action': {'type': 'media', 'command': 'next'}},
    {'title': '⏹ Parar', 'action': {'type': 'media', 'command': 'stop'}},
    {'title': '🔉 Volume −', 'action': {'type': 'media', 'command': 'volume_down'}},
    {'title': '🔇 Silenciar', 'action': {'type': 'media', 'command': 'mute'}},
    {'title': '🔊 Volume +', 'action': {'type': 'media', 'command': 'volume_up'}},
    {'title': '📋 Copiar (Ctrl+C)', 'action': {'type': 'keyboard', 'steps': [{'key': 'C', 'modifiers': ['Ctrl']}]}},
    {'title': '📌 Colar (Ctrl+V)', 'action': {'type': 'keyboard', 'steps': [{'key': 'V', 'modifiers': ['Ctrl']}]}},
    {'title': '✂ Recortar (Ctrl+X)', 'action': {'type': 'keyboard', 'steps': [{'key': 'X', 'modifiers': ['Ctrl']}]}},
    {'title': '↩ Desfazer (Ctrl+Z)', 'action': {'type': 'keyboard', 'steps': [{'key': 'Z', 'modifiers': ['Ctrl']}]}},
    {'title': '↪ Refazer (Ctrl+Y)', 'action': {'type': 'keyboard', 'steps': [{'key': 'Y', 'modifiers': ['Ctrl']}]}},
    {'title': '💾 Salvar (Ctrl+S)', 'action': {'type': 'keyboard', 'steps': [{'key': 'S', 'modifiers': ['Ctrl']}]}},
    {'title': '📸 Print (Win+Shift+S)', 'action': {'type': 'keyboard', 'steps': [{'key': 'S', 'modifiers': ['Shift', 'Win']}]}},
    {'title': '🖥 Desktop (Win+D)', 'action': {'type': 'keyboard', 'steps': [{'key': 'D', 'modifiers': ['Win']}]}},
    {'title': '🔒 Bloquear (Win+L)', 'action': {'type': 'keyboard', 'steps': [{'key': 'L', 'modifiers': ['Win']}]}},
    {'title': '🎙 Mudo Discord (Ctrl+Shift+M)', 'action': {'type': 'keyboard', 'steps': [{'key': 'M', 'modifiers': ['Ctrl', 'Shift']}]}},
    {'title': '🖩 Calculadora', 'action': {'type': 'media', 'command': 'calculator'}},
)

ENCODER_PRESETS = (
    {
        'title': '🔊 Volume & Mudo',
        'subtitle': 'Esq: Vol − · Clique: Mudo · Dir: Vol +',
        'actions': [
            {'type': 'media', 'command': 'volume_down'},
            {'type': 'media', 'command': 'mute'},
            {'type': 'media', 'command': 'volume_up'},
        ],
    },
    {
        'title': '🎵 Controle de Mídia',
        'subtitle': 'Esq: Anterior · Clique: Play/Pause · Dir: Próxima',
        'actions': [
            {'type': 'media', 'command': 'previous'},
            {'type': 'media', 'command': 'play_pause'},
            {'type': 'media', 'command': 'next'},
        ],
    },
    {
        'title': '🔍 Zoom (Ctrl − / 0 / +)',
        'subtitle': 'Esq: Zoom − · Clique: 100% · Dir: Zoom +',
        'actions': [
            {'type': 'keyboard', 'steps': [{'key': 'Minus', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': '0', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Equal', 'modifiers': ['Ctrl']}]},
        ],
    },
    {
        'title': '📑 Navegação de Abas',
        'subtitle': 'Esq: Aba Ant. · Clique: Fechar Aba · Dir: Próx. Aba',
        'actions': [
            {'type': 'keyboard', 'steps': [{'key': 'Tab', 'modifiers': ['Ctrl', 'Shift']}]},
            {'type': 'keyboard', 'steps': [{'key': 'W', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Tab', 'modifiers': ['Ctrl']}]},
        ],
    },
    {
        'title': '🎞 Linha do Tempo / Vídeo',
        'subtitle': 'Esq: ← · Clique: Espaço (Play) · Dir: →',
        'actions': [
            {'type': 'keyboard', 'steps': [{'key': 'Left', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Space', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Right', 'modifiers': []}]},
        ],
    },
    {
        'title': '⏪ Desfazer / Salvar / Refazer',
        'subtitle': 'Esq: Ctrl+Z · Clique: Ctrl+S · Dir: Ctrl+Y',
        'actions': [
            {'type': 'keyboard', 'steps': [{'key': 'Z', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'S', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Y', 'modifiers': ['Ctrl']}]},
        ],
    },
    {
        'title': '🖱 Rolagem do Mouse (Scroll)',
        'subtitle': 'Esq: Roda ↑ · Clique: Botão Meio · Dir: Roda ↓',
        'actions': [
            {'type': 'mouse', 'command': 'wheel_up', 'modifiers': []},
            {'type': 'mouse', 'command': 'middle', 'modifiers': []},
            {'type': 'mouse', 'command': 'wheel_down', 'modifiers': []},
        ],
    },
    {
        'title': '🖥 Desktops Virtuais',
        'subtitle': 'Esq: Desktop ← · Clique: Win+Tab · Dir: Desktop →',
        'actions': [
            {'type': 'keyboard', 'steps': [{'key': 'Left', 'modifiers': ['Ctrl', 'Win']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Tab', 'modifiers': ['Win']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Right', 'modifiers': ['Ctrl', 'Win']}]},
        ],
    },
    {
        'title': '☀ Brilho da Tela',
        'subtitle': 'Esq: Brilho − · Clique: Mostrar Desktop · Dir: Brilho +',
        'actions': [
            {'type': 'media', 'command': 'brightness_down'},
            {'type': 'keyboard', 'steps': [{'key': 'D', 'modifiers': ['Win']}]},
            {'type': 'media', 'command': 'brightness_up'},
        ],
    },
    {
        'title': '↕ Navegação Vertical (↑ / Enter / ↓)',
        'subtitle': 'Esq: Seta ↑ · Clique: Enter · Dir: Seta ↓',
        'actions': [
            {'type': 'keyboard', 'steps': [{'key': 'Up', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Enter', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Down', 'modifiers': []}]},
        ],
    },
    {
        'title': '📄 Rolagem de Página (PgUp / Home / PgDn)',
        'subtitle': 'Esq: Page Up · Clique: Home (Topo) · Dir: Page Down',
        'actions': [
            {'type': 'keyboard', 'steps': [{'key': 'PageUp', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Home', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'PageDown', 'modifiers': []}]},
        ],
    },
    {
        'title': '🖌 Tamanho do Pincel / Editor ([ / B / ])',
        'subtitle': 'Esq: Diminuir [ · Clique: Pincel (B) · Dir: Aumentar ]',
        'actions': [
            {'type': 'keyboard', 'steps': [{'key': 'BracketLeft', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'B', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'BracketRight', 'modifiers': []}]},
        ],
    },
)

LAYER_TEMPLATES = (
    {
        'title': '💼 Produtividade & Edição',
        'subtitle': 'Copiar, Colar, Recortar, Desfazer, Salvar, Print + Giros de Volume e Zoom',
        'positions': [
            {'type': 'keyboard', 'steps': [{'key': 'C', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'V', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'X', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'V', 'modifiers': ['Win']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Z', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Y', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'A', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'S', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'F', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'S', 'modifiers': ['Shift', 'Win']}]},
            {'type': 'keyboard', 'steps': [{'key': 'E', 'modifiers': ['Win']}]},
            {'type': 'keyboard', 'steps': [{'key': 'D', 'modifiers': ['Win']}]},
            # Giro 1: Volume
            {'type': 'media', 'command': 'volume_down'},
            {'type': 'media', 'command': 'mute'},
            {'type': 'media', 'command': 'volume_up'},
            # Giro 2: Zoom
            {'type': 'keyboard', 'steps': [{'key': 'Minus', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': '0', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Equal', 'modifiers': ['Ctrl']}]},
        ],
    },
    {
        'title': '🎵 Multimídia, Jogos & Discord',
        'subtitle': 'Faixas, Play/Pause, Discord Mudo, Gravar Clipe, Calculadora, Bloquear PC',
        'positions': [
            {'type': 'media', 'command': 'previous'},
            {'type': 'media', 'command': 'play_pause'},
            {'type': 'media', 'command': 'next'},
            {'type': 'media', 'command': 'stop'},
            {'type': 'keyboard', 'steps': [{'key': 'M', 'modifiers': ['Ctrl', 'Shift']}]},
            {'type': 'keyboard', 'steps': [{'key': 'D', 'modifiers': ['Ctrl', 'Shift']}]},
            {'type': 'keyboard', 'steps': [{'key': 'G', 'modifiers': ['Alt', 'Win']}]},
            {'type': 'keyboard', 'steps': [{'key': 'R', 'modifiers': ['Alt', 'Win']}]},
            {'type': 'keyboard', 'steps': [{'key': 'S', 'modifiers': ['Shift', 'Win']}]},
            {'type': 'media', 'command': 'calculator'},
            {'type': 'keyboard', 'steps': [{'key': 'Escape', 'modifiers': ['Ctrl', 'Shift']}]},
            {'type': 'keyboard', 'steps': [{'key': 'L', 'modifiers': ['Win']}]},
            # Giro 1: Volume
            {'type': 'media', 'command': 'volume_down'},
            {'type': 'media', 'command': 'mute'},
            {'type': 'media', 'command': 'volume_up'},
            # Giro 2: Mídia
            {'type': 'media', 'command': 'previous'},
            {'type': 'media', 'command': 'play_pause'},
            {'type': 'media', 'command': 'next'},
        ],
    },
    {
        'title': '🌐 Navegador & Web',
        'subtitle': 'Nova aba, Fechar, Reabrir, Alternar abas, Voltar/Avançar, Atualizar + Scroll/Zoom',
        'positions': [
            {'type': 'keyboard', 'steps': [{'key': 'T', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'W', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'T', 'modifiers': ['Ctrl', 'Shift']}]},
            {'type': 'keyboard', 'steps': [{'key': 'N', 'modifiers': ['Ctrl', 'Shift']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Tab', 'modifiers': ['Ctrl', 'Shift']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Tab', 'modifiers': ['Ctrl']}]},
            {'type': 'media', 'command': 'browser_back'},
            {'type': 'media', 'command': 'browser_forward'},
            {'type': 'media', 'command': 'browser_refresh'},
            {'type': 'keyboard', 'steps': [{'key': 'F', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'C', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'V', 'modifiers': ['Ctrl']}]},
            # Giro 1: Scroll
            {'type': 'mouse', 'command': 'wheel_up', 'modifiers': []},
            {'type': 'mouse', 'command': 'middle', 'modifiers': []},
            {'type': 'mouse', 'command': 'wheel_down', 'modifiers': []},
            # Giro 2: Zoom
            {'type': 'keyboard', 'steps': [{'key': 'Minus', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': '0', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Equal', 'modifiers': ['Ctrl']}]},
        ],
    },
    {
        'title': '🔢 Teclado Numérico (0–9)',
        'subtitle': 'Números 0 a 9, Backspace e Enter nas 12 teclas + Volume e Mídia nos Giros',
        'positions': [
            {'type': 'keyboard', 'steps': [{'key': '7', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '8', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '9', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Backspace', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '4', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '5', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '6', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '0', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '1', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '2', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': '3', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Enter', 'modifiers': []}]},
            # Giro 1: Volume
            {'type': 'media', 'command': 'volume_down'},
            {'type': 'media', 'command': 'mute'},
            {'type': 'media', 'command': 'volume_up'},
            # Giro 2: Mídia
            {'type': 'media', 'command': 'previous'},
            {'type': 'media', 'command': 'play_pause'},
            {'type': 'media', 'command': 'next'},
        ],
    },
    {
        'title': '🎬 Edição de Vídeo & Criação',
        'subtitle': 'Timeline nos giros, Desfazer/Refazer, Recortar, Duplicar, Apagar, Play/Pause',
        'positions': [
            {'type': 'keyboard', 'steps': [{'key': 'Z', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Y', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'X', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'D', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'C', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'V', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Delete', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'S', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Left', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Space', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Right', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Enter', 'modifiers': []}]},
            # Giro 1: Timeline
            {'type': 'keyboard', 'steps': [{'key': 'Left', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Space', 'modifiers': []}]},
            {'type': 'keyboard', 'steps': [{'key': 'Right', 'modifiers': []}]},
            # Giro 2: Zoom
            {'type': 'keyboard', 'steps': [{'key': 'Minus', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': '0', 'modifiers': ['Ctrl']}]},
            {'type': 'keyboard', 'steps': [{'key': 'Equal', 'modifiers': ['Ctrl']}]},
        ],
    },
)

# Nomes das rotinas Set_Keyboard_* em widget.o. São modelos para rascunhos.
MODELS = {
    '12+2': (12, 2, 4), '3+1': (3, 1, 3), '6+2': (6, 2, 3), '9+3': (9, 3, 3),
    '0+1': (0, 1, 1), '0+2': (0, 2, 1), '0+3': (0, 3, 1), '1+0': (1, 0, 1),
    '2+0': (2, 0, 2), '3+0': (3, 0, 3), '4+0': (4, 0, 2), '4+1': (4, 1, 2),
    '4+2': (4, 2, 2), '4+3': (4, 3, 2), '5+0': (5, 0, 3), '6+0': (6, 0, 3),
    '6+1': (6, 1, 3), '9+2': (9, 2, 3), '11+3': (11, 3, 4), '12+3': (12, 3, 4),
    '12+4': (12, 4, 4), '15+3': (15, 3, 5), '16+0': (16, 0, 4), '21+1': (21, 1, 7)}


def label_key(key):
    return KEY_LABELS.get(key, key)


def label_step(step):
    return ' + '.join([*(MOD_LABELS.get(m, m) for m in step['modifiers']), *([label_key(step['key'])] if step['key'] else [])])


def label_action(action):
    kind = action['type']
    if kind == 'raw':
        return f"Registro preservado (tipo {bytes.fromhex(action['data_hex'])[3]})"
    if kind == 'none':
        return 'Sem ação'
    if kind == 'keyboard':
        return ' → '.join(label_step(s) for s in action['steps'])
    if kind == 'media':
        return MEDIA[action['command']]
    if kind == 'mouse':
        return ' + '.join([*action['modifiers'], MOUSE[action['command']]])
    return f"Atraso de {action['ms']} ms"


def _hsv_to_rgb(h, s, v):
    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    return v, p, q


def _rgb_to_hsv(r, g, b):
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = (maxc - minc) / maxc
    rc = (maxc - r) / (maxc - minc)
    gc = (maxc - g) / (maxc - minc)
    bc = (maxc - b) / (maxc - minc)
    if r == maxc:
        h = bc - gc
    elif g == maxc:
        h = 2.0 + rc - bc
    else:
        h = 4.0 + gc - rc
    return (h / 6.0) % 1.0, s, v


def hsv_to_hex(hue, saturation, value):
    h = (float(hue) % 360.0) / 360.0
    s = max(0.0, min(100.0, float(saturation))) / 100.0
    v = max(0.0, min(100.0, float(value))) / 100.0
    r, g, b = _hsv_to_rgb(h, s, v)
    return f'#{int(round(r * 255)):02x}{int(round(g * 255)):02x}{int(round(b * 255)):02x}'


def _parse_hex_rgb(hex_color):
    clean = str(hex_color or '').strip().lstrip('#')
    if len(clean) == 3:
        clean = ''.join(ch * 2 for ch in clean)
    if len(clean) != 6 or any(ch not in '0123456789abcdefABCDEF' for ch in clean):
        raise ValueError('Código de cor hexadecimal inválido (use #RRGGBB).')
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)


def hex_to_hsv(hex_color):
    """Converte #RRGGBB para (matiz 0..360, saturação 0..100, brilho 0..100)."""
    r, g, b = _parse_hex_rgb(hex_color)
    h, s, v = _rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return int(round(h * 360.0)) % 360, int(round(s * 100.0)), int(round(v * 100.0))


def closest_hardware_color(hex_color):
    """Mapeia qualquer tonalidade #RRGGBB com precisão para uma das 7 cores físicas (1..7) do teclado."""
    r, g, b = _parse_hex_rgb(hex_color)
    normalized = f'#{r:02x}{g:02x}{b:02x}'
    for key, (_, target_hex) in COLORS.items():
        if normalized == target_hex.lower():
            return key
    for shade in COLOR_SHADES:
        if normalized == shade['hex'].lower():
            return shade['hw']
    h, s, _ = _rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    if s < 0.08:
        return 'cyan'
    deg = (h * 360.0) % 360.0
    if deg >= 325.0 or deg < 16.0:
        return 'red'
    if deg < 42.0:
        return 'orange'
    if deg < 70.0:
        return 'yellow'
    if deg < 165.0:
        return 'green'
    if deg < 196.0:
        return 'cyan'
    if deg < 236.0:
        return 'blue'
    return 'purple'


_QT_SPECIAL_KEYS = {
    0x01000000: 'Escape',
    0x01000001: 'Tab',
    0x01000002: 'Tab',        # Key_Backtab
    0x01000003: 'Backspace',
    0x01000004: 'Enter',      # Key_Return
    0x01000005: 'Enter',      # Key_Enter
    0x01000006: 'Insert',
    0x01000007: 'Delete',
    0x01000008: 'Pause',
    0x01000009: 'PrintScreen',
    0x0100000a: 'PrintScreen',
    0x01000010: 'Home',
    0x01000011: 'End',
    0x01000012: 'Left',
    0x01000013: 'Up',
    0x01000014: 'Right',
    0x01000015: 'Down',
    0x01000016: 'PageUp',
    0x01000017: 'PageDown',
    0x01000024: 'CapsLock',
    0x01000025: 'NumLock',
    0x01000026: 'ScrollLock',
    0x01000055: 'Menu',
    0x20: 'Space',
    0x60: 'Grave', 0x7e: 'Grave',
    0x2d: 'Minus', 0x5f: 'Minus',
    0x3d: 'Equal', 0x2b: 'Equal',
    0x5b: 'BracketLeft', 0x7b: 'BracketLeft',
    0x5d: 'BracketRight', 0x7d: 'BracketRight',
    0x5c: 'Backslash', 0x7c: 'Backslash',
    0x3b: 'Semicolon', 0x3a: 'Semicolon',
    0x27: 'Quote', 0x22: 'Quote',
    0x2c: 'Comma', 0x3c: 'Comma',
    0x2e: 'Period', 0x3e: 'Period',
    0x2f: 'Slash', 0x3f: 'Slash',
}

_QT_MEDIA_KEYS = {
    0x01000080: 'play_pause',       # Key_MediaPlay
    0x01000081: 'stop',             # Key_MediaStop
    0x01000082: 'previous',         # Key_MediaPrevious
    0x01000083: 'next',             # Key_MediaNext
    0x01000085: 'play_pause',       # Key_MediaPause
    0x01000086: 'play_pause',       # Key_MediaTogglePlayPause
    0x01000070: 'volume_down',      # Key_VolumeDown
    0x01000071: 'mute',             # Key_VolumeMute
    0x01000072: 'volume_up',        # Key_VolumeUp
    0x010000b2: 'brightness_up',    # Key_MonBrightnessUp
    0x010000b3: 'brightness_down',  # Key_MonBrightnessDown
    0x01000090: 'browser_home',     # Key_HomePage
    0x010000a0: 'email',            # Key_LaunchMail
    0x010000a1: 'media_player',     # Key_LaunchMedia
    0x010000b6: 'calculator',       # Key_Calculator
    0x01000061: 'browser_back',     # Key_Back
    0x01000062: 'browser_forward',  # Key_Forward
    0x01000064: 'browser_refresh',  # Key_Refresh
}

_QT_MODIFIER_ONLY_KEYS = {
    0x01000020: 'Shift',
    0x01000021: 'Ctrl',
    0x01000022: 'Win',
    0x01000023: 'Alt',
    0x01001103: 'RightAlt',
}


def action_from_qt_event(qt_key, qt_modifiers=0, text=''):
    """Reconhece tecla, atalho (ex. Ctrl+C, Ctrl+V) ou tecla multimídia vinda do teclado físico."""
    qt_key = int(qt_key)
    qt_modifiers = int(qt_modifiers)
    if qt_key in _QT_MODIFIER_ONLY_KEYS:
        return None
    if qt_key in _QT_MEDIA_KEYS:
        return {'type': 'media', 'command': _QT_MEDIA_KEYS[qt_key]}
    mods = []
    if qt_modifiers & 0x04000000:  # Qt.ControlModifier
        mods.append('Ctrl')
    if qt_modifiers & 0x02000000:  # Qt.ShiftModifier
        mods.append('Shift')
    if qt_modifiers & 0x08000000:  # Qt.AltModifier
        mods.append('Alt')
    if qt_modifiers & 0x10000000:  # Qt.MetaModifier
        mods.append('Win')
    keypad = bool(qt_modifiers & 0x20000000)  # Qt.KeypadModifier
    mapped_key = None
    if 0x41 <= qt_key <= 0x5a:
        mapped_key = chr(qt_key)
    elif 0x30 <= qt_key <= 0x39:
        mapped_key = chr(qt_key)
    elif 0x01000030 <= qt_key <= 0x01000047:
        mapped_key = f'F{qt_key - 0x01000030 + 1}'
    elif keypad and qt_key in (0x2b, 0x2d, 0x2a, 0x2f, 0x2e, 0x2c, 0x01000005):
        mapped_key = {
            0x2b: 'NumAdd', 0x2d: 'NumSubtract', 0x2a: 'NumMultiply',
            0x2f: 'NumDivide', 0x2e: 'NumDecimal', 0x2c: 'NumDecimal',
            0x01000005: 'NumEnter'
        }[qt_key]
    elif qt_key in _QT_SPECIAL_KEYS:
        mapped_key = _QT_SPECIAL_KEYS[qt_key]
    elif text and len(text) == 1:
        upper = text.upper()
        if upper in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
            mapped_key = upper
    if not mapped_key:
        return None
    return {'type': 'keyboard', 'steps': [{'key': mapped_key, 'modifiers': mods}]}


_TEXT_CHAR_MAP = {
    **{ch: (ch.upper(), []) for ch in 'abcdefghijklmnopqrstuvwxyz0123456789'},
    **{ch: (ch, ['Shift']) for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'},
    ' ': ('Space', []),
    '\n': ('Enter', []),
    '-': ('Minus', []), '_': ('Minus', ['Shift']),
    '=': ('Equal', []), '+': ('Equal', ['Shift']),
    '[': ('BracketLeft', []), '{': ('BracketLeft', ['Shift']),
    ']': ('BracketRight', []), '}': ('BracketRight', ['Shift']),
    '\\': ('Backslash', []), '|': ('Backslash', ['Shift']),
    ';': ('Semicolon', []), ':': ('Semicolon', ['Shift']),
    "'": ('Quote', []), '"': ('Quote', ['Shift']),
    '`': ('Grave', []), '~': ('Grave', ['Shift']),
    ',': ('Comma', []), '<': ('Comma', ['Shift']),
    '.': ('Period', []), '>': ('Period', ['Shift']),
    '/': ('Slash', []), '?': ('Slash', ['Shift']),
    '!': ('1', ['Shift']), '@': ('2', ['Shift']), '#': ('3', ['Shift']),
    '$': ('4', ['Shift']), '%': ('5', ['Shift']), '^': ('6', ['Shift']),
    '&': ('7', ['Shift']), '*': ('8', ['Shift']), '(': ('9', ['Shift']),
    ')': ('0', ['Shift']),
}


def action_from_text(text, press_enter=False):
    """Converte um texto curto (até 20 caracteres) em sequência de etapas de teclado."""
    if not isinstance(text, str) or not text:
        raise ValueError('Digite pelo menos um caractere para criar a macro de texto.')
    steps = []
    for ch in text:
        if ch not in _TEXT_CHAR_MAP:
            raise ValueError(f'Caractere "{ch}" não suportado na digitação rápida.')
        key, mods = _TEXT_CHAR_MAP[ch]
        steps.append({'key': key, 'modifiers': list(mods)})
    if press_enter:
        steps.append({'key': 'Enter', 'modifiers': []})
    if len(steps) > 20:
        raise ValueError('O texto (incluindo Enter, se marcado) comporta no máximo 20 etapas por tecla.')
    return {'type': 'keyboard', 'steps': steps}

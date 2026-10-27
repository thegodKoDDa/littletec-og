import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ScrollView {
    id: pane
    required property var theme
    required property var studio
    property var editor: studio.state
    property var pickedModifiers: []
    property int selectedStep: -1
    property bool listenKeyboard: true
    property bool autoAdvance: false
    property string activeCategory: "Todas"
    readonly property bool capturingActive: listenKeyboard && !search.activeFocus && !macroInput.activeFocus && !delay.activeFocus
    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    ColumnLayout {
        width: pane.availableWidth; spacing: 12

        Item {
            id: keyCatcher
            objectName: "keyCaptureArea"
            Layout.preferredWidth: 0; Layout.preferredHeight: 0
            focus: true
            Component.onCompleted: keyCatcher.forceActiveFocus()
            Keys.onPressed: event => {
                if (!pane.listenKeyboard || search.activeFocus || macroInput.activeFocus || delay.activeFocus)
                    return
                if (pane.studio.captureKeyEvent(event.key, event.modifiers, event.text, append.checked, pane.autoAdvance)) {
                    event.accepted = true
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true; spacing: 14
            Panel {
                theme: pane.theme
                Layout.fillWidth: true
                Layout.preferredHeight: Math.max(305, Math.ceil(pane.editor.keyCount / pane.editor.columns) * 74 + 44)
                RowLayout {
                    anchors.fill: parent; anchors.margins: 16; spacing: 16
                    GridLayout {
                        visible: pane.editor.keyCount > 0
                        Layout.fillWidth: true; Layout.fillHeight: true; columns: pane.editor.columns; columnSpacing: 8; rowSpacing: 8
                        Repeater {
                            model: pane.editor.keyCount
                            Button {
                                id: keyControl
                                required property int index
                                readonly property var modelData: (pane.editor.positions && index < pane.editor.positions.length)
                                    ? pane.editor.positions[index]
                                    : ({index: index, title: "Tecla", label: "", modified: false})
                                readonly property bool isSelected: pane.editor.selected === keyControl.index
                                focusPolicy: Qt.NoFocus
                                Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumWidth: 38
                                Accessible.name: modelData.title + ": " + modelData.label + (modelData.modified ? ", alterada" : "")
                                background: Rectangle {
                                    radius: 8
                                    color: keyControl.isSelected ? pane.theme.raised : pane.theme.bg
                                    border.color: keyControl.isSelected
                                        ? (pane.capturingActive ? pane.editor.visualColorHex : pane.theme.accent)
                                        : (keyControl.modelData.modified ? pane.theme.accent : pane.theme.stroke)
                                    border.width: keyControl.isSelected ? 2 : 1
                                }
                                contentItem: ColumnLayout {
                                    spacing: 4
                                    Label {
                                        text: keyControl.modelData.title + (keyControl.modelData.modified ? " •" : "") + (keyControl.isSelected && pane.capturingActive ? " ⌨" : "")
                                        color: keyControl.isSelected && pane.capturingActive ? pane.editor.visualColorHex : pane.theme.muted
                                        font.pixelSize: 10
                                    }
                                    Label { text: keyControl.modelData.label; color: pane.theme.ink; font.pixelSize: 12; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; Layout.fillWidth: true }
                                }
                                padding: 8
                                onClicked: {
                                    pane.selectedStep = -1
                                    pane.studio.select(keyControl.index)
                                    keyCatcher.forceActiveFocus()
                                }
                            }
                        }
                    }

                    // Separador vertical entre as 12 teclas e os 2 Knobs
                    Rectangle {
                        visible: pane.editor.encoderCount > 0
                        Layout.preferredWidth: 1; Layout.fillHeight: true
                        color: pane.theme.stroke
                    }

                    // Coluna dedicada aos 2 Knobs (Giratório 1 e Giratório 2)
                    ColumnLayout {
                        visible: pane.editor.encoderCount > 0
                        Layout.preferredWidth: 292
                        Layout.fillHeight: true
                        spacing: 8

                        Repeater {
                            model: pane.editor.encoderCount
                            Rectangle {
                                id: knobCard
                                required property int index
                                readonly property int basePos: pane.editor.keyCount + knobCard.index * 3
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 10
                                color: pane.theme.bg
                                border.color: (pane.editor.selected >= knobCard.basePos && pane.editor.selected < knobCard.basePos + 3)
                                    ? pane.theme.accent : pane.theme.stroke
                                border.width: 1

                                ColumnLayout {
                                    anchors.fill: parent; anchors.margins: 8; spacing: 6

                                    RowLayout {
                                        Layout.fillWidth: true; spacing: 6
                                        Rectangle {
                                            width: 22; height: 22; radius: 11
                                            color: pane.theme.raised
                                            border.color: pane.theme.accent; border.width: 1.5
                                            Label {
                                                anchors.centerIn: parent
                                                text: (knobCard.index + 1).toString()
                                                color: pane.theme.ink; font.pixelSize: 10; font.weight: Font.DemiBold
                                            }
                                        }
                                        Label {
                                            text: "KNOB / GIRO " + (knobCard.index + 1)
                                            color: pane.theme.ink; font.pixelSize: 11; font.weight: Font.DemiBold
                                        }
                                        Item { Layout.fillWidth: true }
                                        StudioButton {
                                            theme: pane.theme
                                            text: "⇄ Inverter ↶/↷"
                                            font.pixelSize: 10
                                            padding: 4
                                            onClicked: {
                                                pane.studio.invertEncoderDirections(knobCard.index)
                                                keyCatcher.forceActiveFocus()
                                            }
                                        }
                                        StudioButton {
                                            id: presetMenuBtn
                                            theme: pane.theme
                                            text: "Preset ▾"
                                            font.pixelSize: 10
                                            padding: 4
                                            onClicked: knobPresetMenu.open()

                                            Menu {
                                                id: knobPresetMenu
                                                y: presetMenuBtn.height
                                                width: 250
                                                Repeater {
                                                    model: pane.studio.encoderPresets
                                                    MenuItem {
                                                        required property var modelData
                                                        text: modelData.title
                                                        font.pixelSize: 12
                                                        onTriggered: {
                                                            pane.studio.applyEncoderPreset(knobCard.index, modelData.index)
                                                            keyCatcher.forceActiveFocus()
                                                        }
                                                    }
                                                }
                                                MenuSeparator {}
                                                MenuItem {
                                                    text: "Limpar este giro"
                                                    font.pixelSize: 12
                                                    onTriggered: {
                                                        pane.studio.clearEncoder(knobCard.index)
                                                        keyCatcher.forceActiveFocus()
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    // 3 Cartões de posição do Knob: Girar Esquerda (↶), Clique (●), Girar Direita (↷)
                                    RowLayout {
                                        Layout.fillWidth: true; Layout.fillHeight: true; spacing: 6
                                        Repeater {
                                            model: [
                                                { symbol: "↶ Esq.", part: 0 },
                                                { symbol: "● Clique", part: 1 },
                                                { symbol: "↷ Dir.", part: 2 }
                                            ]
                                            Button {
                                                id: knobPartBtn
                                                required property var modelData
                                                required property int index
                                                readonly property int position: knobCard.basePos + knobPartBtn.index
                                                readonly property var posData: (pane.editor.positions && position < pane.editor.positions.length)
                                                    ? pane.editor.positions[position]
                                                    : ({index: position, title: "", label: "Sem ação", modified: false})
                                                readonly property bool isSelected: pane.editor.selected === position
                                                focusPolicy: Qt.NoFocus
                                                Layout.fillWidth: true; Layout.fillHeight: true; Layout.preferredWidth: 85
                                                padding: 6
                                                Accessible.name: posData.title + ": " + posData.label
                                                background: Rectangle {
                                                    radius: 7
                                                    color: knobPartBtn.isSelected ? pane.theme.raised : pane.theme.surface
                                                    border.color: knobPartBtn.isSelected
                                                        ? (pane.capturingActive ? pane.editor.visualColorHex : pane.theme.accent)
                                                        : (knobPartBtn.posData.modified ? pane.theme.accent : pane.theme.stroke)
                                                    border.width: knobPartBtn.isSelected ? 2 : 1
                                                }
                                                contentItem: ColumnLayout {
                                                    spacing: 2
                                                    Label {
                                                        text: knobPartBtn.modelData.symbol
                                                            + (knobPartBtn.posData.modified ? " •" : "")
                                                            + (knobPartBtn.isSelected && pane.capturingActive ? " ⌨" : "")
                                                        color: knobPartBtn.isSelected && pane.capturingActive ? pane.editor.visualColorHex : pane.theme.muted
                                                        font.pixelSize: 10; font.weight: Font.DemiBold
                                                        Layout.fillWidth: true; elide: Text.ElideRight
                                                    }
                                                    Label {
                                                        text: knobPartBtn.posData.label
                                                        color: pane.theme.ink
                                                        font.pixelSize: 11
                                                        wrapMode: Text.Wrap
                                                        maximumLineCount: 2
                                                        elide: Text.ElideRight
                                                        Layout.fillWidth: true
                                                    }
                                                }
                                                onClicked: {
                                                    pane.selectedStep = -1
                                                    pane.studio.select(position)
                                                    keyCatcher.forceActiveFocus()
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true; spacing: 6
                            StudioButton {
                                theme: pane.theme
                                text: "Trocar Giro 1 ↔ 2"
                                font.pixelSize: 10
                                padding: 6
                                Layout.fillWidth: true
                                visible: pane.editor.encoderCount >= 2
                                onClicked: {
                                    pane.studio.swapEncoders()
                                    keyCatcher.forceActiveFocus()
                                }
                            }
                            StudioButton {
                                theme: pane.theme
                                text: "Replicar nas 3 camadas"
                                font.pixelSize: 10
                                padding: 6
                                Layout.fillWidth: true
                                onClicked: {
                                    pane.studio.copyEncodersToAllLayers()
                                    keyCatcher.forceActiveFocus()
                                }
                            }
                        }
                    }
                }
            }

            Panel {
                theme: pane.theme; Layout.preferredWidth: 315; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 14; spacing: 6
                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: pane.editor.positions[pane.editor.selected].title; color: pane.theme.ink; font.pixelSize: 17; font.weight: Font.DemiBold }
                        Item { Layout.fillWidth: true }
                        Label { text: pane.editor.action.type === "keyboard" ? pane.editor.action.steps.length + " / 20 etapas" : "AÇÃO ATRIBUÍDA"; color: pane.theme.muted; font.pixelSize: 11 }
                    }

                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 62; radius: 8
                        color: pane.capturingActive ? Qt.rgba(0.13, 0.83, 0.93, 0.12) : pane.theme.bg
                        border.color: pane.capturingActive ? pane.editor.visualColorHex : pane.theme.stroke
                        border.width: pane.capturingActive ? 2 : 1
                        TapHandler { onTapped: { pane.listenKeyboard = true; keyCatcher.forceActiveFocus() } }
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 6; spacing: 2
                            RowLayout {
                                Layout.fillWidth: true
                                CheckBox {
                                    objectName: "listenKeyboardCheck"
                                    checked: pane.listenKeyboard
                                    text: "⌨ Capturar do meu teclado"
                                    font.pixelSize: 11
                                    focusPolicy: Qt.NoFocus
                                    onToggled: {
                                        pane.listenKeyboard = checked
                                        if (checked) keyCatcher.forceActiveFocus()
                                    }
                                }
                                Item { Layout.fillWidth: true }
                                CheckBox {
                                    checked: pane.autoAdvance
                                    text: "Auto-avançar"
                                    font.pixelSize: 10
                                    focusPolicy: Qt.NoFocus
                                    onToggled: { pane.autoAdvance = checked; keyCatcher.forceActiveFocus() }
                                }
                            }
                            Label {
                                Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 10
                                color: pane.capturingActive ? pane.theme.ink : pane.theme.muted
                                text: pane.capturingActive
                                    ? "Aperte qualquer tecla ou atalho (ex.: 4, Ctrl+C, Ctrl+V)…"
                                    : "Clique na tecla ao lado para gravar pelo seu teclado."
                            }
                        }
                    }

                    Item {
                        Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 54
                        ListView {
                            anchors.fill: parent
                            visible: pane.editor.action.type === "keyboard"
                            clip: true
                            model: pane.editor.action.type === "keyboard" ? pane.editor.action.steps : []
                            delegate: RowLayout {
                                required property var modelData
                                required property int index
                                width: ListView.view.width; spacing: 0
                                Label {
                                    text: (index + 1) + ". " + modelData.modifiers.concat(modelData.key ? [modelData.key] : []).join(" + ")
                                    color: pane.selectedStep === index ? pane.theme.accent : pane.theme.ink; font.pixelSize: 12
                                    Layout.fillWidth: true; elide: Text.ElideRight
                                    TapHandler { onTapped: pane.selectedStep = index }
                                }
                                StudioButton { theme: pane.theme; text: "↑"; padding: 4; onClicked: pane.studio.moveStep(index, -1) }
                                StudioButton { theme: pane.theme; text: "↓"; padding: 4; onClicked: pane.studio.moveStep(index, 1) }
                                StudioButton { theme: pane.theme; text: "×"; padding: 4; onClicked: { pane.studio.removeStep(index); pane.selectedStep = -1 } }
                            }
                        }
                        Label {
                            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                            visible: pane.editor.action.type !== "keyboard"
                            text: pane.editor.positions[pane.editor.selected].label
                            color: pane.theme.ink; wrapMode: Text.Wrap
                        }
                    }

                    CheckBox { id: append; text: "Acrescentar à sequência (até 20 etapas)"; font.pixelSize: 11; focusPolicy: Qt.NoFocus; onToggled: keyCatcher.forceActiveFocus() }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 6
                        StudioButton { theme: pane.theme; text: "Copiar tecla"; font.pixelSize: 11; Layout.fillWidth: true; onClicked: { pane.studio.copyPosition(); keyCatcher.forceActiveFocus() } }
                        StudioButton { theme: pane.theme; text: "Colar tecla"; font.pixelSize: 11; Layout.fillWidth: true; enabled: pane.editor.canPaste; onClicked: { pane.studio.pastePosition(); keyCatcher.forceActiveFocus() } }
                    }
                    RowLayout {
                        Layout.fillWidth: true; spacing: 6
                        StudioButton { theme: pane.theme; text: "Limpar posição"; font.pixelSize: 11; Layout.fillWidth: true; onClicked: { pane.studio.clear("position"); keyCatcher.forceActiveFocus() } }
                        StudioButton { theme: pane.theme; text: "Limpar camada"; font.pixelSize: 11; onClicked: pane.studio.clear("layer") }
                        StudioButton { theme: pane.theme; text: "Limpar tudo"; font.pixelSize: 11; onClicked: pane.studio.clear("all") }
                    }
                }
            }
        }

        Panel {
            theme: pane.theme; Layout.fillWidth: true; Layout.preferredHeight: 118
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 12; spacing: 6
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "AÇÕES RÁPIDAS EM 1 CLIQUE (MÍDIA E ATALHOS PARA QUALQUER TECLA OU GIRO)"; color: pane.theme.muted; font.pixelSize: 11; font.weight: Font.DemiBold }
                    Item { Layout.fillWidth: true }
                    Label { text: "Alvo: " + pane.editor.positions[pane.editor.selected].title; color: pane.theme.accent; font.pixelSize: 11 }
                }
                Flow {
                    Layout.fillWidth: true; Layout.fillHeight: true; spacing: 6
                    Repeater {
                        model: pane.studio.quickActions
                        StudioButton {
                            required property var modelData
                            theme: pane.theme
                            text: modelData.title
                            font.pixelSize: 11
                            onClicked: {
                                pane.studio.assignQuick(modelData.index, append.checked)
                                keyCatcher.forceActiveFocus()
                            }
                        }
                    }
                }
            }
        }

        Panel {
            theme: pane.theme; Layout.fillWidth: true; Layout.preferredHeight: 370
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 14; spacing: 8
                RowLayout {
                    Layout.fillWidth: true; spacing: 5
                    Repeater {
                        model: ["Todas", "Atalhos prontos", "Multimídia", "Teclado", "Mouse", "Atalhos e símbolos", "Presets de Giros", "Templates de Camada"]
                        Button {
                            required property string modelData
                            text: modelData
                            checkable: true
                            checked: pane.activeCategory === modelData
                            focusPolicy: Qt.NoFocus
                            font.pixelSize: 11; padding: 6
                            onClicked: {
                                pane.activeCategory = modelData
                                keyCatcher.forceActiveFocus()
                            }
                        }
                    }
                    Item { Layout.fillWidth: true }
                    TextField {
                        id: search
                        visible: pane.activeCategory !== "Presets de Giros" && pane.activeCategory !== "Templates de Camada"
                        placeholderText: "Buscar função, faixa, copiar, F13, mouse…"
                        Layout.preferredWidth: 210
                        selectByMouse: true
                        onAccepted: keyCatcher.forceActiveFocus()
                    }
                }

                RowLayout {
                    visible: pane.activeCategory !== "Presets de Giros" && pane.activeCategory !== "Templates de Camada"
                    Layout.fillWidth: true; spacing: 8
                    TextField {
                        id: macroInput
                        objectName: "macroTextInput"
                        placeholderText: "Digitar texto/número na tecla (ex.: 1234 ou comando)…"
                        Layout.fillWidth: true
                        selectByMouse: true
                        maximumLength: 20
                        onAccepted: {
                            pane.studio.assignTextMacro(macroInput.text, macroEnter.checked, append.checked)
                            keyCatcher.forceActiveFocus()
                        }
                    }
                    CheckBox { id: macroEnter; text: "+ Enter"; font.pixelSize: 11; focusPolicy: Qt.NoFocus }
                    StudioButton {
                        theme: pane.theme; text: "Atribuir texto"; font.pixelSize: 11
                        enabled: macroInput.text.length > 0
                        onClicked: {
                            pane.studio.assignTextMacro(macroInput.text, macroEnter.checked, append.checked)
                            keyCatcher.forceActiveFocus()
                        }
                    }
                    SpinBox { id: delay; from: 0; to: 6000; value: 100; editable: true; Layout.preferredWidth: 120 }
                    StudioButton {
                        theme: pane.theme; text: "Atraso (ms)"; font.pixelSize: 11
                        onClicked: {
                            pane.studio.assignDelay(delay.value)
                            keyCatcher.forceActiveFocus()
                        }
                    }
                }

                Flow {
                    visible: pane.activeCategory !== "Presets de Giros" && pane.activeCategory !== "Templates de Camada"
                    Layout.fillWidth: true; spacing: 2
                    Repeater {
                        model: pane.studio.modifiers
                        CheckBox {
                            required property string modelData
                            text: modelData.replace("Right", "D · "); font.pixelSize: 11; padding: 4
                            focusPolicy: Qt.NoFocus
                            onToggled: pane.pickedModifiers = checked ? pane.pickedModifiers.concat([modelData]) : pane.pickedModifiers.filter(m => m !== modelData)
                        }
                    }
                    StudioButton { theme: pane.theme; text: "Só modificadores"; font.pixelSize: 11; enabled: pane.pickedModifiers.length > 0; onClicked: { pane.studio.assignModifiers(pane.pickedModifiers); keyCatcher.forceActiveFocus() } }
                    StudioButton { theme: pane.theme; text: "Alterar etapa " + (pane.selectedStep + 1); font.pixelSize: 11; visible: pane.selectedStep >= 0; onClicked: { pane.studio.editStepModifiers(pane.selectedStep, pane.pickedModifiers); keyCatcher.forceActiveFocus() } }
                }

                Label { visible: pane.activeCategory === "Atalhos e símbolos"; text: "Símbolos usam posições US; o resultado depende do layout do sistema."; color: pane.theme.muted; font.pixelSize: 11 }

                // Aba Presets de Giros
                ScrollView {
                    visible: pane.activeCategory === "Presets de Giros"
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    GridLayout {
                        width: parent.width; columns: 3; rowSpacing: 8; columnSpacing: 8
                        Repeater {
                            model: pane.studio.encoderPresets
                            Rectangle {
                                required property var modelData
                                Layout.fillWidth: true; Layout.preferredHeight: 84; radius: 8
                                color: pane.theme.bg; border.color: pane.theme.stroke; border.width: 1
                                ColumnLayout {
                                    anchors.fill: parent; anchors.margins: 8; spacing: 4
                                    Label { text: modelData.title; color: pane.theme.ink; font.pixelSize: 12; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                                    Label { text: modelData.subtitle; color: pane.theme.muted; font.pixelSize: 10; elide: Text.ElideRight; Layout.fillWidth: true }
                                    RowLayout {
                                        Layout.fillWidth: true; spacing: 6
                                        StudioButton {
                                            theme: pane.theme; text: "Usar no Giratório 1"; font.pixelSize: 10; padding: 4; Layout.fillWidth: true
                                            onClicked: { pane.studio.applyEncoderPreset(0, modelData.index); keyCatcher.forceActiveFocus() }
                                        }
                                        StudioButton {
                                            theme: pane.theme; text: "Usar no Giratório 2"; font.pixelSize: 10; padding: 4; Layout.fillWidth: true
                                            onClicked: { pane.studio.applyEncoderPreset(1, modelData.index); keyCatcher.forceActiveFocus() }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Aba Templates de Camada
                ScrollView {
                    visible: pane.activeCategory === "Templates de Camada"
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ColumnLayout {
                        width: parent.width; spacing: 8
                        RowLayout {
                            Layout.fillWidth: true; spacing: 8
                            Label { text: "Preencher todas as 18 posições da Camada " + (pane.editor.layer + 1) + " ou clonar camada:"; color: pane.theme.muted; font.pixelSize: 11 }
                            Item { Layout.fillWidth: true }
                            Repeater {
                                model: 3
                                StudioButton {
                                    required property int index
                                    visible: index !== pane.editor.layer
                                    theme: pane.theme
                                    text: "Copiar esta camada para Camada " + (index + 1)
                                    font.pixelSize: 11; padding: 5
                                    onClicked: pane.studio.cloneLayerTo(index)
                                }
                            }
                        }
                        GridLayout {
                            Layout.fillWidth: true; columns: 2; rowSpacing: 8; columnSpacing: 8
                            Repeater {
                                model: pane.studio.layerTemplates
                                Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true; Layout.preferredHeight: 68; radius: 8
                                    color: pane.theme.bg; border.color: pane.theme.stroke; border.width: 1
                                    RowLayout {
                                        anchors.fill: parent; anchors.margins: 10; spacing: 10
                                        ColumnLayout {
                                            Layout.fillWidth: true; spacing: 2
                                            Label { text: modelData.title; color: pane.theme.ink; font.pixelSize: 12; font.weight: Font.DemiBold }
                                            Label { text: modelData.subtitle; color: pane.theme.muted; font.pixelSize: 10; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                        }
                                        StudioButton {
                                            theme: pane.theme; text: "Aplicar na Camada " + (pane.editor.layer + 1); font.pixelSize: 11
                                            onClicked: { pane.studio.applyLayerTemplate(modelData.index); keyCatcher.forceActiveFocus() }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Catálogo padrão
                ScrollView {
                    id: catalog
                    visible: pane.activeCategory !== "Presets de Giros" && pane.activeCategory !== "Templates de Camada"
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    Flow {
                        width: catalog.availableWidth; spacing: 6
                        Repeater {
                            model: pane.studio.search(pane.activeCategory, search.text)
                            StudioButton {
                                required property var modelData
                                theme: pane.theme; text: modelData.title
                                implicitWidth: Math.max(54, implicitContentWidth + 24)
                                onClicked: {
                                    pane.studio.assign(modelData.catalogIndex, pane.pickedModifiers, append.checked)
                                    keyCatcher.forceActiveFocus()
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Panel {
    id: pane
    required property var studio
    property var editor: studio.state
    property bool autoApply: true
    readonly property int activeMode: Number.isInteger(pane.editor.lighting.mode) ? pane.editor.lighting.mode : 1
    objectName: "lightingPage"

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 22; spacing: 18

        RowLayout {
            Layout.fillWidth: true; spacing: 14
            ColumnLayout {
                Layout.fillWidth: true; spacing: 4
                Label {
                    text: "Iluminação LED do Teclado · Camada " + (pane.editor.layer + 1)
                    color: pane.theme.ink; font.pixelSize: 22; font.weight: Font.DemiBold
                }
                Label {
                    text: "O controlador físico deste modelo (CH57x · 1189:8842) possui 7 cores nativas e 6 modos de efeito gravados no chip."
                    color: pane.theme.muted; font.pixelSize: 12
                }
            }
            CheckBox {
                id: autoApplyBtn
                checked: pane.autoApply
                text: "Aplicar automaticamente ao clicar"
                font.pixelSize: 12
                focusPolicy: Qt.NoFocus
                onToggled: pane.autoApply = checked
            }
        }

        // 7 Cores físicas nativas do hardware USB
        ColumnLayout {
            Layout.fillWidth: true; spacing: 8
            Label {
                text: "1. COR DO LED (CAMADA " + (pane.editor.layer + 1) + ")"
                color: pane.theme.muted; font.pixelSize: 11; font.weight: Font.DemiBold
            }
            RowLayout {
                Layout.fillWidth: true; spacing: 12
                Repeater {
                    model: pane.studio.colors
                    Button {
                        id: swatch
                        required property var modelData
                        focusPolicy: Qt.NoFocus
                        Layout.fillWidth: true; Layout.preferredHeight: 96
                        Accessible.name: modelData.name
                        readonly property bool selected: pane.editor.lighting.color === swatch.modelData.id
                        background: Rectangle {
                            color: pane.theme.raised; radius: 12
                            border.color: swatch.selected ? swatch.modelData.color : pane.theme.stroke
                            border.width: swatch.selected ? 3 : 1
                        }
                        contentItem: ColumnLayout {
                            spacing: 6
                            Rectangle {
                                color: swatch.modelData.color; width: 34; height: 34; radius: 17
                                Layout.alignment: Qt.AlignHCenter
                                border.color: "#ffffff66"; border.width: swatch.selected ? 2 : 0
                            }
                            Label {
                                text: swatch.modelData.name; color: pane.theme.ink
                                font.pixelSize: 13; font.weight: swatch.selected ? Font.DemiBold : Font.Normal
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                        onClicked: {
                            let targetMode = pane.activeMode === 0 ? 1 : pane.activeMode
                            pane.studio.setLighting(targetMode, modelData.id, pane.autoApply)
                        }
                    }
                }
            }
        }

        // 6 Modos de efeito nativos do hardware
        ColumnLayout {
            Layout.fillWidth: true; spacing: 8
            Label {
                text: "2. MODO / EFEITO DO LED"
                color: pane.theme.muted; font.pixelSize: 11; font.weight: Font.DemiBold
            }
            GridLayout {
                Layout.fillWidth: true; columns: 3; rowSpacing: 10; columnSpacing: 10
                Repeater {
                    model: pane.studio.ledModes
                    Button {
                        id: modeBtn
                        required property var modelData
                        focusPolicy: Qt.NoFocus
                        Layout.fillWidth: true; Layout.preferredHeight: 54
                        readonly property bool isSelected: pane.activeMode === modeBtn.modelData.id
                        background: Rectangle {
                            radius: 10
                            color: modeBtn.isSelected ? pane.theme.accent : pane.theme.raised
                            border.color: modeBtn.isSelected ? pane.theme.accent : pane.theme.stroke
                            border.width: modeBtn.isSelected ? 2 : 1
                        }
                        contentItem: Label {
                            text: modeBtn.modelData.name
                            color: modeBtn.isSelected ? pane.theme.bg : pane.theme.ink
                            font.pixelSize: 13
                            font.weight: modeBtn.isSelected ? Font.DemiBold : Font.Normal
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: {
                            pane.studio.setLightingMode(modelData.id, pane.autoApply)
                        }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        // Barra de status e aplicação
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 68; radius: 10
            color: pane.theme.bg; border.color: pane.theme.stroke; border.width: 1
            RowLayout {
                anchors.fill: parent; anchors.margins: 12; spacing: 12
                Button {
                    objectName: "applyLightingButton"
                    text: pane.editor.busy ? "Enviando…" : "Aplicar na Camada " + (pane.editor.layer + 1)
                    enabled: pane.editor.canApplyLighting
                    focusPolicy: Qt.NoFocus
                    Layout.minimumWidth: 165
                    padding: 11
                    Accessible.name: "Aplicar iluminação ao teclado"
                    onClicked: pane.studio.applyLighting()
                }
                StudioButton {
                    objectName: "applyAllLayersButton"
                    theme: pane.theme
                    text: "Aplicar esta cor nas 3 Camadas"
                    enabled: pane.editor.canApplyLighting
                    onClicked: pane.studio.applyLightingAllLayers()
                }
                Rectangle {
                    width: 24; height: 24; radius: 12
                    color: pane.editor.hwColorHex || "#22d3ee"
                    border.color: pane.theme.stroke; border.width: 1
                }
                Label {
                    Layout.fillWidth: true; wrapMode: Text.Wrap; color: pane.theme.muted; font.pixelSize: 12
                    text: {
                        let last = pane.editor.lastLighting;
                        let hwInfo = "Selecionado: " + (pane.editor.hwColorName || "Ciano") + " · Modo " + pane.activeMode + " (Pacote USB: " + (pane.editor.hwByteHex || "0x51") + ")";
                        if (!last || !last.color) return hwInfo;
                        let c = pane.studio.colors.find(c => c.id === last.color);
                        return hwInfo + "  |  Último enviado: " + (c ? c.name : last.color) + " · Modo " + last.mode;
                    }
                }
            }
        }
    }
}

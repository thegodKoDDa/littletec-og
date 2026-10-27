import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: root
    required property QtObject studio
    property var data: studio.state
    property bool dark: true
    property string page: "Mapeamento"
    readonly property bool capturingKeys: root.page === "Mapeamento" && mappingPage.capturingActive
    readonly property color bg: dark ? "#111418" : "#f3f5f8"
    readonly property color surface: dark ? "#1a1e24" : "#ffffff"
    readonly property color raised: dark ? "#242a33" : "#eaf0f7"
    readonly property color ink: dark ? "#edf1f7" : "#172334"
    readonly property color muted: dark ? "#9ca9bb" : "#596a80"
    readonly property color stroke: dark ? "#343c49" : "#d5dde8"
    readonly property color accent: dark ? "#81adff" : "#265ec7"
    width: 1280; height: 860; minimumWidth: 1040; minimumHeight: 720
    visible: true; color: bg
    title: "LittleTec Studio · " + data.name
    onClosing: close => { close.accepted = studio.confirmDiscard() }
    font.family: "Segoe UI"; font.pixelSize: 14
    palette.window: bg; palette.windowText: ink; palette.text: ink
    palette.button: raised; palette.buttonText: ink; palette.base: surface
    palette.highlight: accent; palette.highlightedText: bg
    Shortcut { sequences: [StandardKey.Undo]; enabled: !root.capturingKeys; onActivated: studio.undo() }
    Shortcut { sequences: [StandardKey.Redo]; enabled: !root.capturingKeys; onActivated: studio.redo() }
    Shortcut { sequences: [StandardKey.Save]; enabled: !root.capturingKeys; onActivated: studio.saveProfile() }
    Shortcut { sequences: [StandardKey.SaveAs]; enabled: !root.capturingKeys; onActivated: studio.saveProfileAs() }
    Shortcut { sequences: [StandardKey.Open]; enabled: !root.capturingKeys; onActivated: studio.openProfile() }
    Shortcut { sequences: [StandardKey.New]; enabled: !root.capturingKeys; onActivated: studio.newProfile("12+2", 12, 2, 4) }
    RowLayout {
        anchors.fill: parent; spacing: 0
        Rectangle {
            Layout.preferredWidth: 162; Layout.fillHeight: true; color: root.surface
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 14; spacing: 8
                Label { text: "LittleTec"; font.pixelSize: 23; font.weight: Font.DemiBold; color: root.ink; Layout.topMargin: 10 }
                Label { text: "STUDIO 1.1"; color: root.muted; font.pixelSize: 10; Layout.bottomMargin: 24 }
                Repeater {
                    model: ["Mapeamento", "Iluminação", "Perfis"]
                    StudioButton {
                        required property string modelData
                        theme: root; text: modelData; Layout.fillWidth: true
                        onClicked: root.page = modelData
                    }
                }
                Item { Layout.fillHeight: true }
                Label { text: "12 teclas · 2 giros"; color: root.muted; font.pixelSize: 12 }
                Label { text: "3 camadas"; color: root.muted; font.pixelSize: 12 }
                StudioButton { theme: root; text: "Diagnóstico"; Layout.fillWidth: true; onClicked: root.page = "Diagnóstico" }
                StudioButton { theme: root; text: root.dark ? "Tema claro" : "Tema escuro"; Layout.fillWidth: true; onClicked: root.dark = !root.dark }
            }
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; Layout.margins: 20; spacing: 14
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 4
                    Label { text: root.page; color: root.ink; font.pixelSize: 25; font.weight: Font.DemiBold }
                    Label { text: root.data.name + (root.data.dirty ? " · alterações locais" : root.data.filePath ? " · arquivo salvo" : " · rascunho local"); color: root.muted; font.pixelSize: 12 }
                }
                Item { Layout.fillWidth: true }
                BusyIndicator { running: root.data.busy; opacity: root.data.busy ? 1 : 0; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
                Label { text: root.data.connection; color: root.accent; font.pixelSize: 12 }
                Button { objectName: "readKeyboardButton"; text: "Ler teclado"; padding: 10; focusPolicy: Qt.NoFocus; enabled: !root.data.busy; onClicked: studio.readKeyboard() }
                StudioButton { theme: root; text: "Salvar perfil"; onClicked: studio.saveProfile() }
            }
            RowLayout {
                visible: root.page === "Mapeamento" || root.page === "Iluminação"; Layout.fillWidth: true
                Label { text: "CAMADA"; color: root.muted; font.pixelSize: 12 }
                Repeater {
                    model: 3
                    Button {
                        required property int index
                        text: (index + 1).toString(); checkable: true; checked: root.data.layer === index
                        focusPolicy: Qt.NoFocus
                        Layout.preferredWidth: 43; onClicked: studio.switchLayer(index)
                    }
                }
                Item { Layout.fillWidth: true }
                StudioButton { theme: root; text: "Desfazer"; enabled: root.data.canUndo; onClicked: studio.undo() }
                StudioButton { theme: root; text: "Refazer"; enabled: root.data.canRedo; onClicked: studio.redo() }
            }
            RowLayout {
                visible: root.page === "Mapeamento"; Layout.fillWidth: true
                Label { text: root.data.planError || (root.data.connected ? root.data.pendingCount + " posições pendentes" : "Leia o teclado para comparar e aplicar."); color: root.muted; Layout.fillWidth: true; elide: Text.ElideRight }
                StudioButton { theme: root; text: "Carregar leitura"; visible: root.data.connected; enabled: !root.data.busy; onClicked: studio.loadDeviceProfile() }
                StudioButton { theme: root; text: "Revisar"; enabled: root.data.pendingCount > 0; onClicked: review.open() }
                Button { objectName: "applyMappingButton"; text: "Aplicar mapeamento"; focusPolicy: Qt.NoFocus; enabled: root.data.canApply; padding: 11; onClicked: studio.applyMapping() }
            }
            StackLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                currentIndex: ["Mapeamento", "Iluminação", "Perfis", "Diagnóstico"].indexOf(root.page)
                MappingPage { id: mappingPage; theme: root; studio: root.studio; editor: root.data }
                LightingPage { theme: root; studio: root.studio; editor: root.data }
                ProfilesPage { theme: root; studio: root.studio; editor: root.data }
                DiagnosticsPage { theme: root; studio: root.studio; editor: root.data }
            }
            Label { text: studio.message; color: root.muted; Layout.fillWidth: true; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font.pixelSize: 12 }
        }
    }
    Dialog {
        id: review
        parent: Overlay.overlay
        title: "Revisão do mapeamento"
        modal: true; anchors.centerIn: parent
        width: Math.min(800, root.width - 60); height: Math.min(490, root.height - 80)
        standardButtons: Dialog.Close
        contentItem: ColumnLayout {
            ListView {
                Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 10
                model: root.data.review
                delegate: ColumnLayout {
                    required property var modelData
                    width: ListView.view.width
                    Label { text: "Camada " + modelData.layer + " · " + modelData.title; color: root.ink; font.bold: true }
                    Label { text: modelData.before + " → " + modelData.after; color: root.muted; wrapMode: Text.Wrap; Layout.fillWidth: true }
                }
            }
            StudioButton { theme: root; text: "Exportar revisão…"; onClicked: studio.exportReview() }
        }
    }
}

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
Panel {
    id: pane
    required property var studio
    property var editor: studio.state
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 26; spacing: 16
        Label { text: "Conexão e detalhes"; color: pane.theme.ink; font.pixelSize: 23 }
        RowLayout {
            StudioButton { theme: pane.theme; text: "Verificar conexão"; enabled: !pane.editor.busy; onClicked: pane.studio.diagnose() }
            StudioButton { theme: pane.theme; text: "Exportar diagnóstico…"; onClicked: pane.studio.exportDiagnostic() }
        }
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true
            TextArea { text: pane.studio.detail; readOnly: true; wrapMode: TextEdit.Wrap; color: pane.theme.ink; selectByMouse: true; background: Rectangle { color: pane.theme.bg; radius: 8 } }
        }
    }
}

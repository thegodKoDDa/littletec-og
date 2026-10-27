import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
Panel {
    id: pane
    required property var studio
    property var editor: studio.state
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 26; spacing: 16
        Label { text: "Seu conjunto de atalhos"; color: pane.theme.ink; font.pixelSize: 23; font.weight: Font.DemiBold }
        TextField { text: pane.editor.name; placeholderText: "Nome do perfil"; Layout.fillWidth: true; onEditingFinished: pane.studio.rename(text) }
        Label { text: pane.editor.filePath || "Perfil ainda não salvo em arquivo"; color: pane.theme.muted; elide: Text.ElideMiddle; Layout.fillWidth: true }
        Flow {
            Layout.fillWidth: true; spacing: 8
            StudioButton { theme: pane.theme; text: "Abrir perfil…"; enabled: !pane.editor.busy; onClicked: pane.studio.openProfile() }
            StudioButton { theme: pane.theme; text: "Salvar"; onClicked: pane.studio.saveProfile() }
            StudioButton { theme: pane.theme; text: "Salvar como…"; onClicked: pane.studio.saveProfileAs() }
            StudioButton { theme: pane.theme; text: "Importar cópia bruta…"; enabled: !pane.editor.busy; onClicked: pane.studio.importBackup() }
            StudioButton { theme: pane.theme; text: "Exportar revisão…"; enabled: pane.editor.connected && !pane.editor.planError; onClicked: pane.studio.exportReview() }
        }
        Label { text: "NOVO RASCUNHO"; color: pane.theme.muted; font.pixelSize: 12; Layout.topMargin: 10 }
        RowLayout {
            ComboBox { id: model; model: pane.studio.models.concat([{id: "personalizado", keys: 12, encoders: 2, columns: 4}]); textRole: "id"; valueRole: "id"; Layout.preferredWidth: 200 }
            StudioButton { theme: pane.theme; text: "Criar perfil"; enabled: !pane.editor.busy; onClicked: pane.studio.newProfile(model.currentValue, keys.value, encoders.value, columns.value) }
        }
        RowLayout {
            visible: model.currentValue === "personalizado"
            Label { text: "Teclas"; color: pane.theme.muted }
            SpinBox { id: keys; from: 0; to: 60; value: 12; editable: true }
            Label { text: "Giratórios"; color: pane.theme.muted }
            SpinBox { id: encoders; from: 0; to: 4; value: 2; editable: true }
            Label { text: "Colunas"; color: pane.theme.muted }
            SpinBox { id: columns; from: 1; to: 12; value: 4; editable: true }
        }
        Label { text: "Modelos são rascunhos locais. A conexão USB identifica automaticamente o seu 12+2."; color: pane.theme.muted; wrapMode: Text.Wrap; Layout.fillWidth: true }
        Item { Layout.fillHeight: true }
        Label { text: pane.editor.backup ? "Última cópia: " + pane.editor.backup : "Cópias do teclado são salvas automaticamente a cada leitura e aplicação."; color: pane.theme.muted; wrapMode: Text.Wrap; Layout.fillWidth: true; font.pixelSize: 12 }
    }
}

import QtQuick
import QtQuick.Controls.Basic
Button {
    id: control
    required property var theme
    padding: 10
    hoverEnabled: true
    focusPolicy: Qt.NoFocus
    background: Rectangle {
        radius: 7
        color: control.down ? theme.stroke : control.hovered ? theme.raised : "transparent"
        border.color: "transparent"
    }
    contentItem: Text {
        text: control.text; color: control.enabled ? theme.ink : theme.muted
        font: control.font; horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
    }
}

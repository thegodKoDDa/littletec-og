import QtQuick
Rectangle {
    required property var theme
    color: theme.surface
    radius: 12
    border.color: theme.stroke
}

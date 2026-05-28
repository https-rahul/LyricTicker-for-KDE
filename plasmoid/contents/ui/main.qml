import QtQuick 2.15
import QtQuick.Layouts 1.3
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.plasmoid 2.0

PlasmoidItem {
    id: root
    width: 400
    height: 50

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 4
        anchors.rightMargin: 4
        spacing: 0

        Item {
            Layout.fillWidth: true
        }

        PlasmaComponents.Label {
            id: lyricLabel
            text: ""
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.Wrap
            elide: Text.ElideRight
            font.pointSize: 10
            Layout.preferredWidth: 220
            Layout.maximumHeight: 40
        }

        Item {
            Layout.fillWidth: true
        }
    }

    Timer {
        id: lyricTimer
        interval: 200
        running: true
        repeat: true
        onTriggered: {
            var xhr = new XMLHttpRequest()
            xhr.onreadystatechange = function() {
                if (xhr.readyState === XMLHttpRequest.DONE) {
                    if (xhr.status === 200 && xhr.responseText !== lyricLabel.text) {
                        lyricLabel.text = xhr.responseText || ""
                    }
                }
            }
            xhr.open("GET", "http://127.0.0.1:5000/", true)                                             // Port must match HTTP_PORT in backend/constants.py
            xhr.send()
        }
    }
}

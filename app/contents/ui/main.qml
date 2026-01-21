import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kquickcontrolsaddons

PlasmoidItem {
    id: root

    // This connects to your Python "Bridge"
    PlasmaCore.DataSource {
        id: lyricSource
        engine: "mpris2" // We can also use this to check if Spotify is playing
        connectedSources: ["org.mpris.MediaPlayer2.spotify"]
    }

    // This specifically fetches the lyric string from your Python service
    // Note: In a real KDE environment, you'd use a DBus interface here
    compactRepresentation: MouseArea {
        width: lyricLabel.implicitWidth + 20
        height: parent.height

        Text {
            id: lyricLabel
            anchors.centerIn: parent
            text: "Waiting for Lyrics..." // We will bind this to DBus
            color: "white"
            font.pixelSize: 14
        }
    }
}
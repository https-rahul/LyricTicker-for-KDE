import QtQuick 6.5
import QtQuick.Controls 6.5

ApplicationWindow {
    id: window
    color: "transparent"
    // flags: Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint
    visible: true
    width: 500
    height: 180
    title: "finally bangya BCCCC"

    Rectangle {
        anchors.fill: parent
        color: "#121212"
        radius: 10 // Optional: slightly rounded corners for a modern look

        Column {
            anchors.centerIn: parent
            spacing: 10
            width: parent.width - 40

            // Previous Line
            Text {
                text: (lyricsProvider.current_index > 0 && lyricsProvider.lyrics_lines.length > 0) ?
                      lyricsProvider.lyrics_lines[lyricsProvider.current_index - 1] : ""
                color: "#6a6a6a"
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap
                opacity: 0.6
            }

            //Current Line
            Text {
                id: currentLyricText
                text: lyricsProvider.current_lyric || ""
                color: "#1DB954" // Spotify Green
                font.pixelSize: 22
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap

                // Smooth fade when the text changes
                Behavior on text {
                    SequentialAnimation {
                        NumberAnimation { target: currentLyricText; property: "opacity"; from: 0; to: 1.0; duration: 250 }
                    }
                }
            }

            // Next Line
            Text {
                text: (lyricsProvider.lyrics_lines.length > lyricsProvider.current_index + 1) ?
                      lyricsProvider.lyrics_lines[lyricsProvider.current_index + 1] : ""
                color: "#6a6a6a"
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap
                opacity: 0.6
            }
        }
    }
}
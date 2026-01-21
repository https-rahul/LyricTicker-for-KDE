import QtQuick 6.5
import QtQuick.Controls 6.5

ApplicationWindow {
    color: "transparent"
    flags: Qt.FrameLessWindowHint | Qt.WindowStaysOnBottomHint
    visible: true
    width: 500
    height: 180 // Increased slightly for better spacing
    title: "finally bangya BCCCC"

    Rectangle {
        anchors.fill: parent
        color: "#121212" // Spotify-ish dark background

        Column {
            anchors.centerIn: parent
            spacing: 10
            width: parent.width - 40 // Padding on sides

            // previous line
            Text {
                text: lyricsProvider.current_index > 0 ?
                      lyricsProvider.lyrics_lines[lyricsProvider.current_index - 1] : ""
                color: "#6a6a6a"
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap
                opacity: 0.6
            }

            // current line
            Text {
                id: currentLyricText
                text: lyricsProvider.lyrics_lines.length > lyricsProvider.current_index ?
                      lyricsProvider.lyrics_lines[lyricsProvider.current_index] : "Waiting for Spotify..."
                color: "#1DB954" // Spotify Green
                font.pixelSize: 22
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap

                // Optional: Adds a nice smooth pop when the text changes
                Behavior on text {
                    SequentialAnimation {
                        NumberAnimation { target: currentLyricText; property: "opacity"; from: 0.5; to: 1.0; duration: 200 }
                    }
                }
            }

            // next line
            Text {
                text: lyricsProvider.lyrics_lines.length > lyricsProvider.current_index + 1 ?
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

    // REMOVED: The manual 3000ms Timer.
    // Python's sync_logic now triggers the updates.
}
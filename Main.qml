import QtQuick 6.5
import QtQuick.Controls 6.5

ApplicationWindow {
    visible: true
    width: 500
    height: 150
    title: "Spotify Lyrics Ticker"

    Rectangle {
        anchors.fill: parent
        color: "black"

        Column {
            anchors.centerIn: parent
            spacing: 5
            width: parent.width // Make the Column take the full width of the parent Rectangle

            // previous line
            Text {
                text: lyricsProvider.current_index > 0 && lyricsProvider.lyrics_lines.length > lyricsProvider.current_index ?
                      lyricsProvider.lyrics_lines[lyricsProvider.current_index - 1] : ""
                color: "gray"
                font.pixelSize: 16
                horizontalAlignment: Text.AlignHCenter
                width: parent.width // Text element uses the Column's width
                wrapMode: Text.WordWrap // ⭐️ **KEY FIX**: Enables text to wrap to the next line
            }

            // current line
            Text {
                text: lyricsProvider.lyrics_lines.length > lyricsProvider.current_index ?
                      lyricsProvider.lyrics_lines[lyricsProvider.current_index] : "Loading lyrics..." // Provide a placeholder text
                color: "white"
                font.pixelSize: 20
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap // ⭐️ **KEY FIX**
            }

            // next line
            Text {
                text: lyricsProvider.lyrics_lines.length > lyricsProvider.current_index + 1 ?
                      lyricsProvider.lyrics_lines[lyricsProvider.current_index + 1] : ""
                color: "gray"
                font.pixelSize: 16
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
                wrapMode: Text.WordWrap // ⭐️ **KEY FIX**
            }
        }
    }

    Timer {
        interval: 3000   // advance every 3 seconds
        running: true
        repeat: true
        onTriggered: lyricsProvider.next_line()
    }
}
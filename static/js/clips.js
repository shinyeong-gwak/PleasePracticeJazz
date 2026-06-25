function loadAudio()
{
    const fileName =
        document.getElementById(
            "fileSelect"
        ).value;

    const player =
        document.getElementById(
            "player"
        );

    player.src =
        "/music/audio/" +
        encodeURIComponent(fileName);

    player.load();
}

function formatTime(seconds)
{
    const min =
        Math.floor(seconds / 60);

    const sec =
        (seconds % 60)
            .toFixed(2);

    return min + ":" + sec;
}

function parseTime(text)
{
    const parts = text.split(":");

    return parseInt(parts[0]) * 60
        + parseFloat(parts[1]);
}

function moveStart()
{
    const player =
        document.getElementById("player");

    player.currentTime =
        parseTime(
            document.getElementById(
                "startTime"
            ).value
        );
}

function moveEnd()
{
    const player =
        document.getElementById(
            "player"
        );

    player.currentTime =
        parseTime(
            document.getElementById(
                "endTime"
            ).value
        );
}

function captureStart()
{
    const player =
        document.getElementById(
            "player"
        );

    document.getElementById(
        "startTime"
    ).value =
        formatTime(
            player.currentTime
        );
}

function captureEnd()
{
    const player =
        document.getElementById(
            "player"
        );

    document.getElementById(
        "endTime"
    ).value =
        formatTime(
            player.currentTime
        );
}

async function createClip()
{
    const fileName =
        document.getElementById(
            "fileSelect"
        ).value;

    const startTime =
        parseTime(
            document.getElementById(
                "startTime"
            ).value
        );

    const endTime =
        parseTime(
            document.getElementById(
                "endTime"
            ).value
        );

    const clipName =
        document.getElementById(
            "clipName"
        ).value.trim();

    const response =
        await fetch(
            "/music/clips/create",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    fileName,
                    startTime,
                    endTime,
                    clipName
                })
            }
        );

    const result =
        await response.json();

    alert(
        "생성 완료 : " +
        result.fileName
    );
}

function changePlaybackRate()
{
    const player =
        document.getElementById(
            "player"
        );

    player.playbackRate =
        parseFloat(
            document.getElementById(
                "playbackRate"
            ).value
        );
}

async function createPitchVersion()
{
    const fileName =
        document.getElementById(
            "fileSelect"
        ).value;

    const semitones =
        parseInt(
            document.getElementById(
                "pitch"
            ).value
        );

    const response =
        await fetch(
            "/music/clips/pitch",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    fileName,
                    semitones
                })
            }
        );

    const result =
        await response.json();

    alert(
        "생성 완료 : " +
        result.fileName
    );
}

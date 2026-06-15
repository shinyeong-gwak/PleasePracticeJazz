from utils.music_util import youtube_to_mp3
from repositories import music_log_repository


def sync(
        playlist_name: str,
        url: str):

    try:

        music_log_repository.add_log(
            playlist_name,
            url,
            "RUNNING",
            "동기화 시작"
        )

        youtube_to_mp3(url)

        music_log_repository.add_log(
            playlist_name,
            url,
            "SUCCESS",
            "동기화 완료"
        )

    except Exception as e:

        music_log_repository.add_log(
            playlist_name,
            url,
            "FAILED",
            str(e)
        )

        raise
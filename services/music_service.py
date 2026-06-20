from repositories import music_log_repository, playlist_sync_repository
from utils.music_util import (
    MP3_DIR,
    download_youtube_entry,
    extract_playlist_entries,
)


def should_delete_file(filename, playlist_name):

    for item in playlist_sync_repository.iter_other_playlist_items(playlist_name):
        if item.get("filename") == filename:
            return False

    return True


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

        current_entries = extract_playlist_entries(url)
        previous_state = playlist_sync_repository.get_playlist_state(playlist_name)
        previous_items = previous_state.get("items", [])

        previous_by_id = {
            item["id"]: item
            for item in previous_items
            if item.get("id")
        }

        current_ids = {
            entry["id"]
            for entry in current_entries
        }

        synced_items = []
        downloaded_count = 0
        reused_count = 0
        deleted_count = 0

        for entry in current_entries:

            previous_item = previous_by_id.get(entry["id"])

            if previous_item:
                previous_path = MP3_DIR / previous_item["filename"]

                if previous_path.exists():
                    synced_items.append({
                        "id": entry["id"],
                        "title": entry["title"],
                        "url": entry["url"],
                        "filename": previous_item["filename"]
                    })
                    reused_count += 1
                    continue

            downloaded = download_youtube_entry(entry["url"])
            synced_items.append(downloaded)
            downloaded_count += 1

        removed_items = [
            item
            for item in previous_items
            if item.get("id") not in current_ids
        ]

        playlist_sync_repository.save_playlist_state(
            playlist_name,
            {
                "url": url,
                "items": synced_items
            }
        )

        for removed_item in removed_items:
            filename = removed_item.get("filename")

            if not filename:
                continue

            if not should_delete_file(filename, playlist_name):
                continue

            file_path = MP3_DIR / filename

            if file_path.exists():
                file_path.unlink()
                deleted_count += 1

        message = (
            f"동기화 완료 "
            f"(신규 {downloaded_count}, 유지 {reused_count}, 삭제 {deleted_count})"
        )

        music_log_repository.add_log(
            playlist_name,
            url,
            "SUCCESS",
            message
        )

    except Exception as e:

        music_log_repository.add_log(
            playlist_name,
            url,
            "FAILED",
            str(e)
        )

        raise

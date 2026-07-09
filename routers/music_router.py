from fastapi import APIRouter, BackgroundTasks, Form, Request
from starlette.responses import JSONResponse, RedirectResponse

from core.render import render_page
from repositories import (
    daily_repository,
    lick_repository,
    playlist_repository,
    score_repository,
)
from services import music_service


router = APIRouter(prefix="/music")


def _build_daily_payload():
    current_report = daily_repository.get_current_report()
    return {
        "daily_report": current_report,
        "current_archive": daily_repository.build_week_archive(current_report),
        "tune_suggestions": daily_repository.get_tune_suggestions(),
        "recent_lick_files": lick_repository.get_recent_files(),
        "recent_score_files": score_repository.get_recent_files(),
    }


@router.get("/playlist")
def playlist_page(request: Request):
    playlists = playlist_repository.get_all()
    return render_page(
        request,
        "music/playlist.html",
        "플레이리스트",
        {"playlists": playlists},
    )


@router.post("/playlist/add")
def add_playlist(name: str = Form(...), url: str = Form(...)):
    playlist_repository.add(name, url)
    return RedirectResponse("/music/playlist", status_code=303)


@router.post("/playlist/sync")
def sync_playlist(
    background_tasks: BackgroundTasks,
    playlist_name: str = Form(...),
    url: str = Form(...),
):
    background_tasks.add_task(music_service.sync, playlist_name, url)
    return RedirectResponse("/music/playlist", status_code=303)


@router.post("/playlist/delete")
def delete_playlist(name: str = Form(...), url: str = Form(...)):
    playlist_repository.delete(name, url)
    return RedirectResponse("/music/playlist", status_code=303)


@router.get("/licks")
def licks_page(request: Request, file: str = ""):
    licks = lick_repository.get_all()
    return render_page(
        request,
        "music/licks.html",
        "Lick 연습",
        {
            "licks": licks,
            "selected_lick_file": file,
        },
    )


@router.get("/daily")
@router.get("/daliy")
def daily_page(request: Request):
    return render_page(
        request,
        "music/daily.html",
        "연습일지",
        _build_daily_payload(),
    )


@router.get("/report")
def report_page(request: Request):
    return render_page(
        request,
        "music/report.html",
        "주간 리포트",
        {"calendar_summary": {"days": [], "weeks": []}},
    )


@router.get("/daily/data")
def daily_page_data():
    return JSONResponse(_build_daily_payload())


@router.get("/report/data")
def report_page_data():
    return JSONResponse(
        {
            "calendar_summary": daily_repository.build_calendar_summary(),
        }
    )


@router.get("/insights")
def insights_page(request: Request):
    return render_page(
        request,
        "music/insights.html",
        "인사이트",
        {
            "insights": daily_repository.get_insights(),
        },
    )


@router.post("/daily/homework")
async def add_daily_homework(request: Request):
    payload = await request.json()
    return JSONResponse(daily_repository.add_homework(payload))


@router.put("/daily/homework/{homework_id}")
async def update_daily_homework(homework_id: str, request: Request):
    payload = await request.json()
    return JSONResponse(daily_repository.update_homework(homework_id, payload))


@router.post("/daily/homework/merge")
async def merge_daily_homework(request: Request):
    payload = await request.json()
    return JSONResponse(
        daily_repository.merge_homework(
            payload.get("sourceId", ""),
            payload.get("targetId", ""),
        )
    )


@router.delete("/daily/homework/{homework_id}")
def delete_daily_homework(homework_id: str):
    return JSONResponse(daily_repository.delete_homework(homework_id))


@router.post("/daily/practice")
async def add_daily_practice(request: Request):
    payload = await request.json()
    return JSONResponse(daily_repository.add_practice(payload))


@router.put("/daily/practice/{practice_id}")
async def update_daily_practice(practice_id: str, request: Request):
    payload = await request.json()
    return JSONResponse(daily_repository.update_practice(practice_id, payload))


@router.delete("/daily/practice/{practice_id}")
def delete_daily_practice(practice_id: str):
    return JSONResponse(daily_repository.delete_practice(practice_id))


@router.post("/daily/ensemble")
async def add_daily_ensemble(request: Request):
    payload = await request.json()
    return JSONResponse(daily_repository.add_ensemble(payload))


@router.put("/daily/ensemble/{ensemble_id}")
async def update_daily_ensemble(ensemble_id: str, request: Request):
    payload = await request.json()
    return JSONResponse(daily_repository.update_ensemble(ensemble_id, payload))


@router.delete("/daily/ensemble/{ensemble_id}")
def delete_daily_ensemble(ensemble_id: str):
    return JSONResponse(daily_repository.delete_ensemble(ensemble_id))


@router.post("/insights")
async def add_insight(request: Request):
    payload = await request.json()
    return JSONResponse(daily_repository.add_insight(payload))


@router.put("/insights/{category}/{insight_id}")
async def update_insight(category: str, insight_id: str, request: Request):
    payload = await request.json()
    return JSONResponse(daily_repository.update_insight(category, insight_id, payload))


@router.delete("/insights/{category}/{insight_id}")
def delete_insight(category: str, insight_id: str):
    return JSONResponse(daily_repository.delete_insight(category, insight_id))

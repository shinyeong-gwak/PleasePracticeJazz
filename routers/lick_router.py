from pathlib import Path

from fastapi import APIRouter, Request
from fastapi import HTTPException
from fastapi.responses import FileResponse

from repositories import lick_repository
from core.render import render_page

from utils.xml.musicxml_exporter import (
    export_musicxml,
    export_circle_of_fifths_musicxml,
)
from data.model.models import LeadSheet
from utils.xml.parser import parse_lead_sheet
from utils.xml.transpose import generate_circle_of_fifths

router = APIRouter()


@router.get("/licks")
def licks_page(request):
    licks = lick_repository.get_all()

    return render_page(
        request,
        "music/licks.html",
        "Lick 연습",
        {"licks": licks}
    )

@router.post("/music/licks/save")
async def save_lick(request: Request):

    data = await request.json()

    return lick_repository.save(data)

@router.get("/music/licks/metadata")
def get_lick_metadata():

    return lick_repository.get_metadata()


@router.delete("/music/licks/{file_name}/{lick_id}")
def delete_lick(file_name: str, lick_id: str):

    return lick_repository.delete(file_name, lick_id)

@router.post("/music/licks/export")
async def export_lick_musicxml(
        request: Request):

    data = await request.json()

    key = data["key"]
    time = data["time"]

    chords = data["chords"]

    rh = data["rh"]
    rh_r = data["rh_r"]

    lh = data["lh"]
    lh_r = data["lh_r"]

    try:
        sheet : LeadSheet = parse_lead_sheet(
            key=key,
            time=time,
            grid=data.get("grid"),

            chords=chords,

            rh=rh,
            rh_r=rh_r,

            lh=lh,
            lh_r=lh_r
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    name = (
            data.get("name")
            or "untitled"
    )

    file_name = (
            data.get("file")
            or "unknown.mp3"
    )

    safe_file_name = (
        file_name
        .replace(".mp3", "")
        .replace("/", "_")
        .replace("\\", "_")
    )

    safe_name = (
        name
        .replace("/", "_")
        .replace("\\", "_")
    )

    output_path = (
        f"downloads/scores/"
        f"{safe_name}[{safe_file_name}].musicxml"
    )

    export_musicxml(
        sheet,
        output_path
    )

    return {
        "success": True,
        "path": output_path
    }

@router.post("/music/licks/export12")
async def export_12_keys_musicxml(
        request: Request):

    data = await request.json()

    try:
        sheet : LeadSheet = parse_lead_sheet(
            key=data["key"],
            time=data["time"],
            grid=data.get("grid"),

            chords=data["chords"],

            rh=data["rh"],
            rh_r=data["rh_r"],

            lh=data["lh"],
            lh_r=data["lh_r"]
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    scores = generate_circle_of_fifths(
        sheet
    )

    name = (
            data.get("name")
            or "untitled"
    )

    file_name = (
            data.get("file")
            or "unknown.mp3"
    )

    safe_file_name = (
        file_name
        .replace(".mp3", "")
        .replace("/", "_")
        .replace("\\", "_")
    )

    safe_name = (
        name
        .replace("/", "_")
        .replace("\\", "_")
    )

    output_path = (
        f"downloads/scores/"
        f"-12key {safe_name}"
        f"[{safe_file_name}].musicxml"
    )

    export_circle_of_fifths_musicxml(
        scores,
        output_path
    )

    return {
        "success": True,
        "path": output_path
    }


@router.get("/music/licks/export-file")
def download_export_file(path: str):

    file_name = Path(path).name
    file_path = Path("downloads/scores") / file_name

    return FileResponse(
        file_path,
        media_type="application/vnd.recordare.musicxml+xml",
        filename=file_name
    )

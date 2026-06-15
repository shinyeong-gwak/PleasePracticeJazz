from fastapi import FastAPI, UploadFile, File
import verovio
import tempfile

app = FastAPI()

# Verovio 초기 설정
vrv_toolkit = verovio.toolkit()
vrv_toolkit.setOptions({
    "scale": 40,
    "pageWidth": 2000,
    "pageHeight": 10000
})


def render_musicxml_to_svg(xml_data: str) -> str:
    """
    MusicXML 문자열을 SVG로 변환
    """
    vrv_toolkit.loadData(xml_data)
    vrv_toolkit.redoLayout()

    svg = vrv_toolkit.renderToSVG(1)  # 1페이지

    return svg
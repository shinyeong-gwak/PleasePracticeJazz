from fastapi import FastAPI, UploadFile, File
import tempfile

app = FastAPI()

# Verovio 초기 설정
# vrv_toolkit = verovio.toolkit()
# vrv_toolkit.setOptions({
#     "pageWidth": 2100,
#     "pageHeight": 2970,
#     "pageMarginTop": 120,
#     "pageMarginBottom": 80,
#     "pageMarginLeft": 80,
#     "pageMarginRight": 80,
#     "adjustPageHeight": True,
# })


def render_musicxml_to_svg(xml_data: str) -> str:
    """
    MusicXML 문자열을 SVG로 변환
    """
    # vrv_toolkit.loadData(xml_data)
    # vrv_toolkit.redoLayout()
    #
    # svg = vrv_toolkit.renderToSVG(1)  # 1페이지

    svg = "empty"
    return svg
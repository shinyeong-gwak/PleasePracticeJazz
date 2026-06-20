import verovio

vrv_toolkit = verovio.toolkit()
vrv_toolkit.setOptions({
    "pageWidth": 1600,
    "pageHeight": 2200,
    "pageMarginTop": 40,
    "pageMarginBottom": 40,
    "pageMarginLeft": 40,
    "pageMarginRight": 40,
    "adjustPageHeight": True,
    "scale": 42
})


def render_musicxml_to_svg(xml_data: str) -> str:
    """
    MusicXML 문자열을 SVG로 변환
    """
    vrv_toolkit.loadData(xml_data)
    vrv_toolkit.redoLayout()

    page_count = vrv_toolkit.getPageCount()

    if page_count == 0:
        return "<div class='render-empty'>렌더링할 페이지가 없습니다.</div>"

    pages = [
        (
            "<section class='render-page'>"
            f"{vrv_toolkit.renderToSVG(page_index)}"
            "</section>"
        )
        for page_index in range(1, page_count + 1)
    ]

    return "<div class='rendered-score'>" + "".join(pages) + "</div>"

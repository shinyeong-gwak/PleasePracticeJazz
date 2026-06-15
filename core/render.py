# core/render.py
from fastapi.templating import Jinja2Templates
from navigation import NAVIGATION

templates = Jinja2Templates(directory="templates")

def render_page(request, template_name: str, page_title: str, context: dict = None):
    if context is None:
        context = {}

    context.update({
        "request": request,
        "navigation": NAVIGATION,
        "page_title": page_title
    })

    return templates.TemplateResponse(
        name=template_name,
        request=request,
        context=context
    )
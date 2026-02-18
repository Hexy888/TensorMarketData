from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

TEMPLATES_DIR = Path("templates/email")
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

def render_email(template_name: str, **ctx) -> str:
    tpl = env.get_template(template_name)
    return tpl.render(**ctx)

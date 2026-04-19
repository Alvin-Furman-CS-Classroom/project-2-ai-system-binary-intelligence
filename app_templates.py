"""
Shared Jinja environment with auto_reload enabled.

Without auto_reload, Jinja keeps compiled templates in memory and HTML edits
do not appear until the server process restarts.
"""

from jinja2 import Environment, FileSystemLoader
from starlette.templating import Jinja2Templates

_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=True,
    auto_reload=True,
)
templates = Jinja2Templates(env=_env)

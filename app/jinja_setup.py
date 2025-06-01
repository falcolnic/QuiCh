import os

from fasthx import Jinja
from starlette.templating import Jinja2Templates

basedir = os.path.abspath(os.path.dirname(__file__))

templates = Jinja2Templates(directory=os.path.join(basedir, "templates"))

jinja = Jinja(templates)

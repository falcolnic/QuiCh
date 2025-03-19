import os
from fasthx import Jinja
from starlette.templating import Jinja2Templates

basedir = os.path.abspath(os.path.dirname(__file__))

# Create a FastAPI Jinja2Templates instance. This will be used in FastHX Jinja instance.
templates = Jinja2Templates(directory=os.path.join(basedir, "templates"))

# FastHX Jinja instance is initialized with the Jinja2Templates instance.
jinja = Jinja(templates)

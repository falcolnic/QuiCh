from fasthtml.common import *

from app.api.youtube import youtube_app
from app.components.js import javascripts
from app.components.navbar import home_template
from app.components.youtube_input import youtube_inpute

app, rt = fast_app(
    live=True,
    debug=True,
    pico=False,
    hdrs=javascripts,
    routes=[Mount("/ui", youtube_app, name="youtube")],
)


@app.get("/")
async def main(request: Request):
    return home_template(request), youtube_inpute()


@app.get("/news")
async def news(request: Request):
    return home_template(request)


@app.get("/blog")
async def blog(request: Request):
    code_block = Pre(
        Code(
            """@app.get('/')
def get():
    return Div(page, cls="uk-container max-w-[600px] uk-margin-top")"""
        )
    )
    page = Article(
        H1("Hello World", cls="uk-article-title"),
        P(
            "Written by ",
            A("Super User", href="#", cls="uk-link"),
            " on 12 April 2012. Posted in ",
            A("Blog", href="#", cls="uk-link"),
            cls="uk-article-meta uk-margin",
        ),
        P(
            """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.""",
            cls="uk-margin uk-text-lead",
        ),
        P(
            """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat.""",
            code_block,
            cls="uk-margin",
        ),
        cls="uk-article",
    )

    return home_template(request), Div(page, cls="uk-container max-w-[600px] uk-margin-top")


if __name__ == "__main__":
    serve()
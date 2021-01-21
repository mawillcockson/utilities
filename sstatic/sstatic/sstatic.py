import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

routes = [
    Mount("/", app=StaticFiles(directory="."), name="static"),
]

app = Starlette(routes=routes)


def main() -> None:
    uvicorn.run("sstatic.sstatic:app", host="0.0.0.0", port=8080, log_level="info")


if __name__ == "__main__":
    main()

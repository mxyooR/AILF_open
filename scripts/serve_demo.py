"""Serve a built frontend with SPA fallback, using only Python's standard library."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class SPAHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        route = urlsplit(self.path).path
        if not route.startswith("/api/") and not Path(route).suffix and not Path(self.translate_path(self.path)).exists():
            self.path = "/index.html"
        return super().send_head()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parents[1] / "frontend" / "build")
    parser.add_argument("--port", type=int, default=3000)
    args = parser.parse_args()
    if not (args.directory / "index.html").is_file():
        parser.error("No frontend build found. Run pnpm build first, or provide --directory.")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(SPAHandler, directory=str(args.directory.resolve())))
    print(f"AILF browser demo: http://localhost:{args.port}/demo", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

"""Developer comparison mount; task semantics remain in Ergora's existing app."""
import argparse
from pathlib import Path

from fastapi.staticfiles import StaticFiles
import uvicorn
from ergora.web import create_app

parser = argparse.ArgumentParser()
parser.add_argument('--home', type=Path, required=True)
parser.add_argument('--port', type=int, default=8981)
args = parser.parse_args()
application = create_app(args.home)
application.mount('/comparison', StaticFiles(directory=Path(__file__).parent / 'dist', html=True), name='comparison')
uvicorn.run(application, host='127.0.0.1', port=args.port)

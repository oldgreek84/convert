import asyncio
from typing import Annotated
import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware


from common import load_paths
import time

load_paths()

from main import main
from interface import WebUI
from processor import JobProcessorRemote
from worker import ThreadWorker
from converter import Converter


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_converter():
    interface = WebUI()
    processor = JobProcessorRemote()
    worker = ThreadWorker()
    return Converter(interface, processor, worker)


async def generate_messages():
    for i in range(5):
        message = f"message: {i}\n"
        yield message
        await asyncio.sleep(1)


@app.get("/")
async def root():
    return {"message": "Hello world"}


@app.get("/stream")
async def stream_messages():
    return StreamingResponse(
        generate_messages(),
        media_type="text/event-stream")


@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    print(f"----- F {len(file)}")
    return {"file_size": len(file)}


@app.post("/uploadfile/")
async def create_file_some(file: UploadFile):
    print(f"----- UP {file.filename}")
    return {"filename": file.filename}

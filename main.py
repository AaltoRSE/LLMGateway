import os
import time
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status

from digitala.freeform import generate_freeform
from digitala.readaloud import generate_readaloud
from digitala.utils import model_loader, parser_loader
from digitala.ta_katja import load_models as load_task_accomplishment_models
from digitala.ta import load_model as load_multilingual_ta_model
import logging

import shutil

from pathlib import Path

#logging.basicConfig(
#    level="INFO",
#    format="%(asctime)s %(filename)s %(levelname)s: %(message)s",
#    datefmt="%Y-%m-%d %H:%M:%S",
#    handlers=[logging.StreamHandler()],
#)


app = FastAPI(
    title="Digitala",
    description="In-progress API developed by Aalto-Speech Group",
    version="0.0.1",
)
models = {}
models['multi'] = {"ta" : {"model" : load_multilingual_ta_model}}
for lang in ["fi", "sv"]:
    model, processor = model_loader(lang)
    parser = parser_loader(lang)
    task_accomplishment_models = load_task_accomplishment_models(lang)
    multilingual_ta_model = load_multilingual_ta_model()
    models[lang] = {
                    "model": model, 
                    "processor": processor,
                    "parser": parser,
                    "ta": task_accomplishment_models
                    }

load_dotenv()


@app.post("/")
async def root(
    file: UploadFile = File(...),
    prompt: Optional[str] = None,
    lang: str = Query("fi", enum=["fi", "sv"]),
    task: str = Query("freeform", enum=["freeform", "readaloud"]),
    key: str = None,
) -> dict:

    file.filename = Path("/tmp") / Path(file.filename).name
    with open(file.filename, "wb") as fout:
        shutil.copyfileobj(file.file, fout)

    start_time = time.time()

    # 14.04.2022 Moodle handles wav audio as application/octet-stream
    """
    if (
        "audio/" not in file.content_type
        and file.content_type != "application/octet-stream"
    ):
        print(file.content_type)
        raise HTTPException(400, detail="Invalid file type")
    """

    logging.info(file.__dict__)

    if key != os.getenv("PASSWORD"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden"
        )

    if task == "readaloud":
        info = generate_readaloud(str(file.filename), model, processor, lang, prompt)
        end_time = time.time()

        response = {
            **{
                "file_name": file.filename,
                "Language": lang,
                "Task": task,
                "prompt": prompt,
                "runtime": end_time - start_time,
            },
            **info,
        }

    elif task == "freeform":
        info = generate_freeform(str(file.filename), models, lang, prompt)
        end_time = time.time()

        response = {
            **{
                "file_name": file.filename,
                "Language": lang,
                "Task": task,
                "prompt": prompt,
                "runtime": end_time - start_time,
            },
            **info,
        }

    if file.filename.is_file():
        file.filename.unlink()

    return response

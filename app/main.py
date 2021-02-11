from fastapi import FastAPI
import logging
import logging.config

logging.config.fileConfig(fname='log.conf')

logger = logging.getLogger("main")

app = FastAPI()


@app.get("/")
async def root():
    logger.info('root requested')
    return {"message": "Hello World"}

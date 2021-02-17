FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# TODO: Switch app dirs when switching to api router
# COPY ./app /app/app
COPY ./app /app
COPY ./requirements.txt requirements.txt
COPY ./log.conf log.conf

RUN python -m pip install --upgrade pip
RUN pip install -r ./requirements.txt

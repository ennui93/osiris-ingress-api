# osiris-ingress-api <!-- omit in toc -->
- [Usage](#usage)
  - [Location of ingressed data](#location-of-ingressed-data)
  - [Notes on uploading data](#notes-on-uploading-data)
  - [Uploading arbitrary data](#uploading-arbitrary-data)
  - [Uploading JSON data](#uploading-json-data)
    - [Supported JSON Schema versions](#supported-json-schema-versions)
- [Configuration](#configuration)
  - [Logging](#logging)
- [Development](#development)
  - [Running locally](#running-locally)
  - [tox](#tox)
  - [Commands](#commands)
    - [Linting](#linting)
    - [Tests](#tests)


## Usage

Generated endpoint documentation can be viewed from the endpoints `/docs` and `/redoc` on the running application.

Please refer to the generated docs regarding request validation and errors.

All the endpoints are based on specifying a `GUID`-resource. Substitute the `{guid}` placeholders with the ID of the DataCatalog dataset or the Azure Storage Account directory you want to upload data to.

### Location of ingressed data
When data is written by the application to storage it will be automatically partitioned by ingress time in the following format:
```
{guid}/year={now.year:02d}/month={now.month:02d}/day={now.day:02d}/hour={now.hour:02d}
```

This format is chosen to ensure future support for data tools, like Apache Spark.


### Notes on uploading data
The file data must be sent in the request body as `multipart/form-data` under the key `file`, i.e.:
```
curl -X 'POST' \
  '<URI>' \
  -H 'Accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@testfile.bin;type=application/octet-stream'
```

Different endpoints may have specific header requirements, see below.

### Uploading arbitrary data
* `/{guid}`

This endpoint uploads data without validation.
Useful for uploading binary data or pre-validated data. If the uploaded data is much too complex and/or large, the in-memory validations supported by this application will probably fail.


### Uploading JSON data
* `/{guid}/json`
* `/{guid}/json?schema_validate=true`

This endpoint uploads JSON data. The request fails if the data is not valid JSON.

It has the optional URL parameter `schema_validate` which, if set to `true`, will additionally validate the data against a valid JSON Schema.

The schema file must be placed at the root of the `{guid}` directory and be named `schema.json`.

#### Supported JSON Schema versions
The supported schema versions is dependant on the pinned version of [fastjsonschema package](https://pypi.org/project/fastjsonschema/)(see `requirements.txt` for version).

The schema file should preferably have a `$schema` directive, for example:
```
"$schema": "http://json-schema.org/draft-07/schema#"
```
`fastjsonschema` will fall-back to its' latest supported version, if the above directive is not present in the schema file.


## Configuration

The application needs a configuration file `conf.ini` (see `conf.example.ini`). This file must 
be placed in the root of the project or in the location `/etc/osiris/conf.ini`.

```
[Logging]
; This points to the logging configuration file.
; It allows you to setup logging for your specific needs.
; Follow the format as specified in: 
configuration_file = <configuration_file>.conf

[FastAPI]
; You can set the root path of the URI the application will be reached on
; in case you're behind a proxy.
; Read more at: https://fastapi.tiangolo.com/advanced/behind-a-proxy/#behind-a-proxy
root_path = <root_path>

[Azure Storage]
; The account URL for the Azure Storage Account to use as a storage backend.
account_url = https://<storage_name>.dfs.core.windows.net/
; The file system or container you want to use with Osiris Ingress.
filesystem_name = <container_name>
```

### Logging
Logging can be controlled by defining handlers and formatters using [Logging Configuration](https://docs.python.org/3/library/logging.config.html) and specifically the [config fileformat](https://docs.python.org/3/library/logging.config.html#logging-config-fileformat). 
The location of the log configuration file (`Logging.configuration_file`) must be defined in the configuration file of the application as mentioned above.

Here is an example configuration:

```
[loggers]
keys=root,main

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=fileFormatter,consoleFormatter

[logger_root]
level=DEBUG
handlers=consoleHandler

[logger_main]
level=DEBUG
handlers=consoleHandler
qualname=main
propagate=0

[handler_consoleHandler]
class=StreamHandler
formatter=consoleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
formatter=fileFormatter
args=('logfile.log',)

[formatter_fileFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=

[formatter_consoleFormatter]
format=%(levelname)s: %(name)s - %(message)s
```

## Development

### Running locally

The application can be run locally by using a supported application server, for example `uvicorn`.

The following commands will install `uvicorn` and start serving the application locally.
```
pip install uvicorn==0.13.3
uvicorn app.main:app --reload
```

### tox

Development for this project relies on [tox](https://tox.readthedocs.io/).

Make sure to have it installed.

### Commands

If you want to run all commands in tox.ini

```sh
$ tox
```

#### Linting

You can also run a single linter specified in tox.ini. For example:

```sh
$ tox -e flake8
```


#### Tests

Run unit tests.

```sh
$ tox -e py3
```

Run a specific testcase.

```sh
tox -e py3 -- -x tests/test_main.py
```

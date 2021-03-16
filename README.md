# osiris-ingress-api <!-- omit in toc -->
- [Configuration](#configuration)
  - [Logging](#logging)
- [Development](#development)
  - [tox](#tox)
  - [Commands](#commands)
    - [Linting](#linting)
    - [Tests](#tests)

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
file_system_name = <container_name>
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

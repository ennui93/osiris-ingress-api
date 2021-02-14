# osiris-ingress-api

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

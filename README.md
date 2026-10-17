# tallyprime

[![CI](https://github.com/jumpfast-tech/tallyprime-api/actions/workflows/ci.yml/badge.svg)](https://github.com/jumpfast-tech/tallyprime-api/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tallyprime.svg)](https://pypi.org/project/tallyprime/)
[![Python versions](https://img.shields.io/pypi/pyversions/tallyprime.svg)](https://pypi.org/project/tallyprime/)

A Python client for the [TallyPrime](https://tallysolutions.com/) HTTP/XML
gateway.

## Installation

```bash
pip install tallyprime
```

## Usage

```python
from tallyprime import TallyClient

with TallyClient(host="localhost", port=9000) as client:
    response_xml = client.send("<ENVELOPE>...</ENVELOPE>")
    print(response_xml)
```

By default the client talks to `http://localhost:9000`, which is where
TallyPrime exposes its gateway when "Enable ODBC/HTTP" is turned on.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest          # run tests
ruff check .    # lint
ruff format .   # format
mypy            # type-check
```

## License

[MIT](LICENSE)

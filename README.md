# oas-client

Generate typed python client from OpenAPI specification

## Installation

You can install the package via pip:

```
pip install oas-client
```

## Usage

Use this command to generate client.

```
oas-client <path_or_url>
```

To use the generate client,

```py
from client.client import APIClient

client = APIClient(
    base_url="https://api.example.com",
    headers={
        "Authorization": "Bearer MY_SECRET_TOKEN",
    },
    # supports all configurations from httpx.Client
)
print(
    client.core_api_list_servers(
        follow_redirects=False,
        timeout=10,
        # supports all configurations from httpx request
    )
)

```

## Why not pydantic?

Request bodies are meant to support partial data, especially in `PATCH` requests, which is not supported by `pydantic` model. So, we use `TypedDict` with `NotRequired` modifier.

```py
class PartialUpdateAccountSchema(TypedDict):
    email: NotRequired[str]
    address: NotRequired[str]
    country: NotRequired[str]
    dob: NotRequired[str]
```

## Why duplicate schemas in requests.py and responses.py?

There is a possibility of duplicate schemas for request body and reponse body because `NotRequired` modifier is necessary for only request body and is not relevant for respose body.

## Limitations

- Only supports OAS 3
- No aysnc support

## License

This project is licensed under the terms of the MIT license.

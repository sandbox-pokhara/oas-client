from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, RootModel


class SecuritySchemeType(str, Enum):
    API_KEY = "apiKey"
    HTTP = "http"
    OAUTH2 = "oauth2"
    OPEN_ID_CONNECT = "openIdConnect"


class SecuritySchemeIn(str, Enum):
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


class ParameterIn(str, Enum):
    QUERY = "query"
    HEADER = "header"
    PATH = "path"
    COOKIE = "cookie"


class Contact(BaseModel):
    name: str | None = None
    url: HttpUrl | None = None
    email: str | None = None


class License(BaseModel):
    name: str
    url: HttpUrl | None = None


class Info(BaseModel):
    title: str
    description: str | None = None
    terms_of_service: HttpUrl | None = Field(None, alias="termsOfService")
    contact: Contact | None = None
    license: License | None = None
    version: str


class ServerVariable(BaseModel):
    enum: list[str] = []
    default: str
    description: str | None = None


class Server(BaseModel):
    url: str
    description: str | None = None
    variables: dict[str, ServerVariable] = {}


class ExternalDocumentation(BaseModel):
    description: str | None = None
    url: HttpUrl


class Reference(BaseModel):
    ref: str = Field(alias="$ref")


class Discriminator(BaseModel):
    property_name: str = Field(alias="propertyName")
    mapping: dict[str, str] | None = {}


class XML(BaseModel):
    name: str | None = None
    namespace: HttpUrl | None = None
    prefix: str | None = None
    attribute: bool | None = None
    wrapped: bool | None = None


class Schema(BaseModel):
    # Core schema properties
    title: str | None = None
    multiple_of: float | None = Field(None, alias="multipleOf")
    maximum: float | None = None
    exclusive_maximum: bool | None = Field(None, alias="exclusiveMaximum")
    minimum: float | None = None
    exclusive_minimum: bool | None = Field(None, alias="exclusiveMinimum")
    max_length: int | None = Field(None, alias="maxLength", ge=0)
    min_length: int | None = Field(None, alias="minLength", ge=0)
    pattern: str | None = None
    max_items: int | None = Field(None, alias="maxItems", ge=0)
    min_items: int | None = Field(None, alias="minItems", ge=0)
    unique_items: bool | None = Field(None, alias="uniqueItems")
    max_properties: int | None = Field(None, alias="maxProperties", ge=0)
    min_properties: int | None = Field(None, alias="minProperties", ge=0)
    required: list[str] = []
    enum: list[Any] = []

    # Type and format
    type: str | None = None
    format: str | None = None

    # Composition
    all_of: list["Schema |Reference"] = []
    one_of: list["Schema |Reference"] = []
    any_of: list["Schema |Reference"] = Field([], alias="anyOf")
    not_: "Schema | Reference | None" = Field(None, alias="not")

    # Object properties
    properties: dict[str, "Schema | Reference"] = {}
    additional_properties: "bool | Schema | Reference | None" = Field(
        None, alias="additionalProperties"
    )

    # Array properties
    items: "Schema | Reference | None" = None

    # Other properties
    description: str | None = None
    default: Any | None = None
    nullable: bool | None = None
    discriminator: Discriminator | None = None
    read_only: bool | None = Field(None, alias="readOnly")
    write_only: bool | None = Field(None, alias="writeOnly")
    xml: XML | None = None
    external_docs: ExternalDocumentation | None = Field(None, alias="externalDocs")
    example: Any | None = None
    deprecated: bool | None = None


class Example(BaseModel):
    summary: str | None = None
    description: str | None = None
    value: Any | None = None
    external_value: HttpUrl | None = Field(None, alias="externalValue")


class MediaType(BaseModel):
    schema_: Schema | Reference | None = Field(None, alias="schema")
    example: Any | None = None
    examples: dict[str, Example | Reference] = {}
    encoding: dict[str, "Encoding"] = {}


class Header(BaseModel):
    description: str | None = None
    required: bool | None = None
    deprecated: bool | None = None
    allow_empty_value: bool | None = Field(None, alias="allowEmptyValue")
    style: str | None = None
    explode: bool | None = None
    allow_reserved: bool | None = Field(None, alias="allowReserved")
    schema_: Schema | Reference | None = Field(None, alias="schema")
    example: Any | None = None
    examples: dict[str, Example | Reference] = {}
    content: dict[str, MediaType] = {}


class Encoding(BaseModel):
    content_type: str | None = Field(None, alias="contentType")
    headers: dict[str, Header | Reference] = {}
    style: str | None = None
    explode: bool | None = None
    allow_reserved: bool | None = Field(None, alias="allowReserved")


class RequestBody(BaseModel):
    description: str | None = None
    content: dict[str, MediaType]
    required: bool | None = None


class Link(BaseModel):
    operation_ref: str | None = Field(None, alias="operationRef")
    operation_id: str | None = Field(None, alias="operationId")
    parameters: dict[str, Any] = {}
    request_body: Any | None = Field(None, alias="requestBody")
    description: str | None = None
    server: Server | None = None


class Response(BaseModel):
    description: str
    headers: dict[str, Header | Reference] = {}
    content: dict[str, MediaType] = {}
    links: dict[str, Link | Reference] = {}


class Parameter(BaseModel):
    name: str
    in_: ParameterIn = Field(alias="in")
    description: str | None = None
    required: bool | None = None
    deprecated: bool | None = None
    allow_empty_value: bool | None = Field(None, alias="allowEmptyValue")
    style: str | None = None
    explode: bool | None = None
    allow_reserved: bool | None = Field(None, alias="allowReserved")
    schema_: Schema | Reference | None = Field(None, alias="schema")
    example: Any | None = None
    examples: dict[str, Example | Reference] = {}
    content: dict[str, MediaType] = {}


class SecurityRequirement(RootModel[dict[str, list[str]]]):
    pass


class OAuthFlow(BaseModel):
    authorization_url: HttpUrl | None = Field(None, alias="authorizationUrl")
    token_url: HttpUrl | None = Field(None, alias="tokenUrl")
    refresh_url: HttpUrl | None = Field(None, alias="refreshUrl")
    scopes: dict[str, str]


class OAuthFlows(BaseModel):
    implicit: OAuthFlow | None = None
    password: OAuthFlow | None = None
    client_credentials: OAuthFlow | None = Field(None, alias="clientCredentials")
    authorization_code: OAuthFlow | None = Field(None, alias="authorizationCode")


class SecurityScheme(BaseModel):
    type: SecuritySchemeType
    description: str | None = None
    name: str | None = None  # For apiKey
    in_: SecuritySchemeIn | None = Field(None, alias="in")  # For apiKey
    scheme: str | None = None  # For http
    bearer_format: str | None = Field(None, alias="bearerFormat")  # For http bearer
    flows: OAuthFlows | None = None  # For oauth2
    open_id_connect_url: HttpUrl | None = Field(
        None, alias="openIdConnectUrl"
    )  # For openIdConnect


class Callback(RootModel[dict[str, "PathItem"]]):
    pass


class Operation(BaseModel):
    tags: list[str] = []
    summary: str | None = None
    description: str | None = None
    external_docs: ExternalDocumentation | None = Field(None, alias="externalDocs")
    operation_id: str | None = Field(None, alias="operationId")
    parameters: list[Parameter | Reference] = []
    request_body: RequestBody | Reference | None = Field(None, alias="requestBody")
    responses: dict[str, Response | Reference]
    callbacks: dict[str, Callback | Reference] = {}
    deprecated: bool | None = None
    security: list[SecurityRequirement] = []
    servers: list[Server] = []


class PathItem(BaseModel):
    ref: str | None = Field(None, alias="$ref")
    summary: str | None = None
    description: str | None = None
    get: Operation | None = None
    put: Operation | None = None
    post: Operation | None = None
    delete: Operation | None = None
    options: Operation | None = None
    head: Operation | None = None
    patch: Operation | None = None
    trace: Operation | None = None
    servers: list[Server] = []
    parameters: list[Parameter | Reference] = []


class Tag(BaseModel):
    name: str
    description: str | None = None
    external_docs: ExternalDocumentation | None = Field(None, alias="externalDocs")


class Components(BaseModel):
    schemas: dict[str, Schema | Reference] = {}
    responses: dict[str, Response | Reference] = {}
    parameters: dict[str, Parameter | Reference] = {}
    examples: dict[str, Example | Reference] = {}
    request_bodies: dict[str, RequestBody | Reference] = Field(
        {}, alias="requestBodies"
    )
    headers: dict[str, Header | Reference] = {}
    security_schemes: dict[str, SecurityScheme | Reference] = Field(
        {}, alias="securitySchemes"
    )
    links: dict[str, Link | Reference] = {}
    callbacks: dict[str, Callback | Reference] = {}


class OpenAPI(BaseModel):
    # FIXME: added default values to all
    # to prevent ty from throwing `missing-argument`
    # error
    openapi: str = ""
    info: Info | None = None
    servers: list[Server] = []
    paths: dict[str, PathItem] = {}
    components: Components | None = None
    security: list[SecurityRequirement] = []
    tags: list[Tag] = []
    external_docs: ExternalDocumentation | None = Field(None, alias="externalDocs")

    class Config:
        validate_by_name = True


# Update forward references
Schema.model_rebuild()
MediaType.model_rebuild()
Callback.model_rebuild()
PathItem.model_rebuild()

# API Reference

- [ObjectType](#ObjectType)
- [SubscriptionType](#SubscriptionType)
- [InputType](#InputType)
- [ScalarType](#ScalarType)
- [InterfaceType](#InterfaceType)
- [UnionType](#UnionType)
- [DirectiveType](#DirectiveType)
- [DeferredType](#DeferredType)
- [BaseType](#BaseType)
- [make_executable_schema](#make_executable_schema)
- [convert_case](#convert_case)


## `ObjectType`

New `ObjectType` is base class for Python classes representing GraphQL types (either `type` or `extend type`).


### `__schema__`

`ObjectType` key attribute is `__schema__` string that can define only one GraphQL type:

```python
class QueryType(ObjectType):
    __schema__ = """
    type Query {
        year: Int!
    }
    """
```

`ObjectType` implements validation logic for `__schema__`. It verifies that its valid SDL string defining exactly one GraphQL type. 


### Resolvers

Resolvers are class methods or static methods named after schema's fields:

```python
class QueryType(ObjectType):
    __schema__ = """
    type Query {
        year: Int!
    }
    """

    @staticmethod
    def resolve_year(_, info: GraphQLResolveInfo) -> int:
        return 2022
```

If resolver function is not present for field, default resolver implemented by `graphql-core` will be used in its place.

In situations when field's name should be resolved to different value, custom mappings can be defined via `__aliases__` attribute:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String!
    }
    """
    __aliases__ = {
        "dateJoined": "date_joined"
    }
```

Above code will result in Ariadne generating resolver resolving `dateJoined` field to `date_joined` attribute on resolved object.

If `date_joined` exists as `resolve_date_joined` callable on `ObjectType`, it will be used as resolver for `dateJoined`:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String
    }
    """
    __aliases__ = {
        "dateJoined": "date_joined"
    }

    @staticmethod
    def resolve_date_joined(user, info) -> Optional[str]:
        if can_see_activity(info.context):
            return user.date_joined

        return None
```


### `__requires__`

When GraphQL type requires on other GraphQL type (or scalar/directive etc. ect.) `ObjectType` will raise an error about missing dependency. This dependency can be provided through `__requires__` attribute:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String!
    }
    """


class UsersGroupType(ObjectType):
    __schema__ = """
    type UsersGroup {
        id: ID!
        users: [User!]!
    }
    """
    __requires__ = [UserType]
```

`ObjectType` verifies that types specified in `__requires__` actually define required types. If `__schema__` in `UserType` is not defining `User`, error will be raised about missing dependency.

In case of circular dependencies, special `DeferredType` can be used:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String!
        group: UsersGroup
    }
    """
    __requires__ = [DeferredType("UsersGroup")]


class UsersGroupType(ObjectType):
    __schema__ = """
    type UsersGroup {
        id: ID!
        users: [User!]!
    }
    """
    __requires__ = [UserType]
```

`DeferredType` makes `UserType` happy about `UsersGroup` dependency, deferring dependency check to `make_executable_schema`. If "real" `UsersGroup` is not provided at that time, error will be raised about missing types required to create schema.


## `SubscriptionType`

Specialized subclass of `ObjectType` that defines GraphQL subscription:

```python
class ChatSubscriptions(SubscriptionType):
    __schema__ = """
    type Subscription {
        chat: Chat
    }
    """
    __requires__ = [ChatType]

    @staticmethod
    async def subscribe_chat(*_):
        async for event in subscribe("chats"):
            yield event["chat_id"]

    @staticmethod
    async def resolve_chat(chat_id, *_):
        # Optional
        return await get_chat_from_db(chat_id)
```


## `InputType`

Defines GraphQL input:

```python
class UserCreateInput(InputType):
    __schema__ = """
    input UserInput {
        name: String!
        email: String!
        fullName: String!
    }
    """
    __args__ = {
        "fullName": "full_name",
    }
```

### `__args__`

Optional attribue `__args__` is a `Dict[str, str]` used to override key names for `dict` representing input's data.

Following JSON:

```json
{
    "name": "Alice",
    "email:" "alice@example.com",
    "fullName": "Alice Chains"
}
```

Will be represented as following dict:

```python
{
    "name": "Alice",
    "email": "alice@example.com",
    "full_name": "Alice Chains",
}
```


## `ScalarType`

Allows you to define custom scalar in your GraphQL schema.

```python
class DateScalar(ScalarType):
    __schema__ = "scalar Datetime"

    @staticmethod
    def serialize(value) -> str:
        # Called by GraphQL to serialize Python value to
        # JSON-serializable format
        return value.strftime("%Y-%m-%d")

    @staticmethod
    def parse_value(value) -> str:
        # Called by GraphQL to parse JSON-serialized value to
        # Python type
        parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
        return parsed_datetime.date()
```

Note that those methods are only required if Python type is not JSON serializable, or you want to customize its serialization process.

Additionally you may define third method called `parse_literal` that customizes value's deserialization from GraphQL query's AST, but this is only useful for complex types that represent objects:

```python
from graphql import StringValueNode


class DateScalar(Scalar):
    __schema__ = "scalar Datetime"

    @staticmethod
    def def parse_literal(ast, variable_values: Optional[Dict[str, Any]] = None):
        if not isinstance(ast, StringValueNode):
            raise ValueError()

        parsed_datetime = datetime.strptime(ast.value, "%Y-%m-%d")
        return parsed_datetime.date()
```

If you won't define `parse_literal`, GraphQL will use custom logic that will unpack value from AST and then call `parse_value` on it.


## `InterfaceType`

Defines intefrace in GraphQL schema:

```python
class SearchResultInterface(InterfaceType):
    __schema__ = """
    interface SearchResult {
        summary: String!
        score: Int!
    }
    """

    @staticmethod
    def resolve_type(obj, info):
        # Returns string with name of GraphQL type representing Python type
        # from your business logic
        if isinstance(obj, UserModel):
            return UserType.graphql_name

        if isinstance(obj, CommentModel):
            return CommentType.graphql_name

        return None

    @staticmethod
    def resolve_summary(obj, info):
        # Optional default resolver for summary field, used by types implementing
        # this interface when they don't implement their own
```


## `UnionType`

Defines GraphQL union:

```python
class SearchResultUnion(UnionType):
    __schema__ = "union SearchResult = User | Post | Thread"
    __requires__ = [UserType, PostType, ThreadType]

    @staticmethod
    def resolve_type(obj, info):
        # Returns string with name of GraphQL type representing Python type
        # from your business logic
        if isinstance(obj, UserModel):
            return UserType.graphql_name

        if isinstance(obj, PostModel):
            return PostType.graphql_name

        if isinstance(obj, ThreadModel):
            return ThreadType.graphql_name

        return None
```


## `DirectiveType`

Defines new GraphQL directive in your schema and specifies `SchemaDirectiveVisitor` for it:


```python
from ariadne import SchemaDirectiveVisitor
from graphql import default_field_resolver


class PrefixStringSchemaVisitor(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        original_resolver = field.resolve or default_field_resolver

        def resolve_prefixed_value(obj, info, **kwargs):
            result = original_resolver(obj, info, **kwargs)
            if result:
                return f"PREFIX: {result}"
            return result

        field.resolve = resolve_prefixed_value
        return field


class PrefixStringDirective(DirectiveType):
    __schema__ = "directive @example on FIELD_DEFINITION"
    __visitor__ = PrefixStringSchemaVisitor
```


## `make_executable_schema`

New `make_executable_schema` takes list of Ariadne's types and constructs executable schema from them, performing last-stage validation for types consistency:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        username: String!
    }
    """


class QueryType(ObjectType):
    __schema__ = """
    type Query {
        user: User
    }
    """
    __requires__ = [UserType]

    @staticmethod
    def user(*_):
        return {
            "id": 1,
            "username": "Alice",
        }


schema = make_executable_schema(QueryType)
```


### Automatic merging of roots

Passing multiple `Query`, `Mutation` or `Subscription` definitions to `make_executable_schema` by default results in schema defining single types containing sum of all fields defined on those types, ordered alphabetically by field name.

```python
class UserQueriesType(ObjectType):
    __schema__ = """
    type Query {
        user(id: ID!): User
    }
    """
    ...


class ProductsQueriesType(ObjectType):
    __schema__ = """
    type Query {
        product(id: ID!): Product
    }
    """
    ...

schema = make_executable_schema(UserQueriesType, ProductsQueriesType)
```

Above schema will have single `Query` type looking like this:

```graphql
type Query {
    product(id: ID!): Product
    user(id: ID!): User
}
```

To opt out of this behavior use `merge_roots=False` option:

```python
schema = make_executable_schema(
    UserQueriesType,
    ProductsQueriesType,
    merge_roots=False,
)
```

## `DeferredType`

`DeferredType` names required GraphQL type as provided at later time:

- Via `make_executable_schema` call
- Or via other type's `__requires__`

It's mostly used to define lazy relationships in reusable modules and to break circular relationships.


### Type with `DeferredType` and other type passed to `make_executable_schema`:

```python
class QueryType(ObjectType):
    __schema__ = """
    type Query {
        id: ID!
        users: [User!]!
    }
    """
    __requires__ = [DeferredType("User")]


class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String!
    }
    """


schema = make_excutable_schema(QueryType, UserType)
```


### Type with `DeferredType` and other type passed as dependency of third type:

```python
class UsersGroupType(ObjectType):
    __schema__ = """
    type UsersGroup {
        id: ID!
        users: [User!]!
    }
    """
    __requires__ = [UserType]


class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String!
    }
    """


class QueryType(ObjectType):
    __schema__ = """
    type Query {
        id: ID!
        users: [User!]!
        groups: [UsersGroup!]!
    }
    """
    __requires__ = [DeferredType("User"), UsersGroupType]


schema = make_excutable_schema(QueryType)
```


## `BaseType`

Base type that all other types extend. You can use it to create custom types:

```python
from typing import Dict

from ariadne_graphql_modules import BaseType
from django.db.models import Model
from graphql import GraphQLFieldResolver

class ModelType(BaseType)
    __abstract__ = True
    __schema__ = str
    __model__ = Model

    resolvers: Dict[str, GraphQLFieldResolver]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls.__dict__.get("__abstract__"):
            return

        cls.__abstract__ = False

        if not cls.__model__:
            raise ValueError(
                f"{cls.__name__} was declared without required '__model__' attribute"
            )

        cls.__schema__ = cls.__create_schema_from_model__()
        cls.resolvers = cls.__get_resolvers__()

    @classmethod
    def __create_schema_from_model__(cls) -> str:
        ... # Your logic that creates GraphQL SDL from Django model

    @classmethod
    def __get_resolvers__(cls) -> Dict[str, GraphQLFieldResolver]:
        ... # Your logic that creates resolvers map from model and cls

    @classmethod
    def __bind_to_schema__(cls, schema):
        # Bind resolvers map to schema, called by `make_executable_schema`
        graphql_type = schema.type_map.get(cls.graphql_name)

        for field_name, field_resolver in cls.resolvers.items():
            graphql_type.fields[field_name].resolve = field_resolver
```


## `make_executable_schema`

```python
def make_executable_schema(
    *types: BaseType, 
    merge_roots: bool = True,
) -> GraphQLSchema:
    ...
```

Utility function that takes args with types and creates executable schema.


### `merge_roots: bool = True`

If set to true (default), `make_executable_schema` will automatically merge multiple `Query`, `Mutation` and `Subscription` types instead of raising error.

Final merged types fields will be ordered alphabetically:

```python
class YearType(ObjectType):
    __schema__ = """
        type Query {
            year: Int!
        }
    """

    @staticmethod
    def resolve_year(*_):
        return 2022


class MonthType(ObjectType):
    __schema__ = """
        type Query {
            month: Int!
        }
    """

    @staticmethod
    def resolve_month(*_):
        return 10


schema = make_executable_schema(YearType, MonthType)

assert print_schema(schema) == """
type Query {
    month: Int!
    year: Int!
}
"""
```

When `merge_roots=False` is explicitly set, `make_executable_schema` will raise an GraphQL error that `type Query` is defined more than once.


## `convert_case`

Utility function that can be used to automatically setup case conversion rules for types.


#### Resolving fields values

Use `__aliases__ = convert_case` to automatically set aliases for fields that convert case

```python
from ariadne_graphql_modules import ObjectType, convert_case, gql


class UserType(ObjectType):
    __schema__ = gql(
        """
        type User {
            id: ID!
            fullName: String!
        }
        """
    )
    __aliases__ = convert_case
```


#### Converting fields arguments

Use `__fields_args__ = convert_case` on type to automatically convert field arguments to python case in resolver kwargs:

```python
from ariadne_graphql_modules import MutationType, convert_case, gql

from my_app import create_user


class UserRegisterMutation(MutationType):
    __schema__ = gql(
        """
        type Mutation {
            registerUser(fullName: String!, email: String!): Boolean!
        }
        """
    )
    __fields_args__ = convert_case

    @staticmethod
    async def resolve_mutation(*_, full_name: str, email: str):
        user = await create_user(
            full_name=full_name,
            email=email,
        )
        return bool(user)
```


#### Converting inputs fields

Use `__args__ = convert_case` on type to automatically convert input fields to python case in resolver kwargs:

```python
from ariadne_graphql_modules import InputType, MutationType, convert_case, gql

from my_app import create_user


class UserRegisterInput(InputType):
    __schema__ = gql(
        """
        input UserRegisterInput {
            fullName: String!
            email: String!
        }
        """
    )
    __args__ = convert_case


class UserRegisterMutation(MutationType):
    __schema__ = gql(
        """
        type Mutation {
            registerUser(input: UserRegisterInput!): Boolean!
        }
        """
    )
    __requires__ = [UserRegisterInput]

    @staticmethod
    async def resolve_mutation(*_, input: dict):
        user = await create_user(
            full_name=input["full_name"],
            email=input["email"],
        )
        return bool(user)
```
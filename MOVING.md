Moving guide
============

`make_executable_schema` provided by Ariadne GraphQL Modules supports combining old and new approaches for schema definition. This allows developers using either to make a switch.


## Updating `make_executable_schema`

To be able to mix old and new approaches in your implementation, replace `make_executable_schema` imported from `ariadne` with one from `ariadne_graphql_modules`:

Old code:

```python
from ariadne import load_schema_from_path, make_executable_schema

type_defs = load_schema_from_path("schema.graphql")

schema = make_executable_schema(type_defs, type_a, type_b, type_c)
```

New code:

```python
from ariadne import load_schema_from_path
from ariadne_graphql_modules import make_executable_schema

type_defs = load_schema_from_path("schema.graphql")

schema = make_executable_schema(
    type_defs, type_a, type_b, type_c,
)
```

If you are passing `type_defs` or types as lists (behavior supported by `ariadne.make_executable_schema`), you'll need to unpack them before passing:

```python
from ariadne import load_schema_from_path
from ariadne_graphql_modules import make_executable_schema

type_defs = load_schema_from_path("schema.graphql")

schema = make_executable_schema(
    type_defs, type_a, *user_types,
)
```


If you are using directives, `directives` option is named `extra_directives` in new function:

```python
from ariadne import load_schema_from_path
from ariadne_graphql_modules import make_executable_schema

type_defs = load_schema_from_path("schema.graphql")

schema = make_executable_schema(
    type_defs, type_a, type_b, type_c,
    extra_directives={"date": MyDateDirective},
)
```

Your resulting schema will remain the same. But you can now pass new types defined using modular approach to add or replace existing ones.


## Using old types in requirements

Use `DeferredType` to satisfy requirement on types defined old way:

```python
from ariadne_graphql_modules import DeferredType, ObjectType, gql


class UserType(ObjectType):
    __schema__ = gql(
        """
        type User {
            id: ID!
            name: String!
            group: UserGroup!
        }
        """
    )
    __requires__ = [DeferredType("UserGroup")]
```


## Old types depending on new ones

In case when old type depends on new one, you only need to make new type known to `make_executable_schema`. This can be done by passing it directly to types list or through requires of other type.

```python
from ariadne import QueryType, gql
from ariadne_graphql_modules import ObjectType, make_executable_schema

type_defs = gql(
    """
    type Query {
        user: User!
    }
    """
)

query_type = QueryType()

@query_type.field("user")
def resolve_user(*_):
    return {
        "id": 1,
        "name": "Alice",
    }


class UserType(ObjectType):
    __schema__ = gql(
        """
        type User {
            id: ID!
            name: String!
        }
        """
    )


schema = make_executable_schema(
    UserType, type_defs, query_type
)
```


## Combining roots

If `combine_roots` option of `make_executable_schema` is enabled (default), `Query`, `Mutation` and `Subscription` types defined both old and new way will be combined in final schema:

```python
from ariadne import QueryType, gql
from ariadne_graphql_modules import ObjectType, make_executable_schema

type_defs = gql(
    """
    type Query {
        random: Int!
    }
    """
)

query_type = QueryType()

@query_type.field("random")
def resolve_random(*_):
    return 6


class NewQueryType(ObjectType):
    __schema__ = gql(
        """
        type Query {
            year: Int!
        }
        """
    )

    @staticmethod
    def resolve_year(*_):
        return 2022


schema = make_executable_schema(
    NewQueryType, type_defs, query_type
)
```

Final `Query` type:

```graphql
type Query {
    random: Int!
    year: Int!
}
```
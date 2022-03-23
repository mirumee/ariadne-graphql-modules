[![Ariadne](https://ariadnegraphql.org/img/logo-horizontal-sm.png)](https://ariadnegraphql.org)

- - - - -

# Ariadne GraphQL Modules

Ariadne package for implementing Ariadne GraphQL schemas using modular approach.

For reasoning behind this work, please see [this GitHub discussion](https://github.com/mirumee/ariadne/issues/306).

See [API reference](./REFERENCE.md) file for documentation.


## Examples

### Basic example

```python
from datetime import date

from ariadne.asgi import GraphQL, gql
from ariadne_graphql_modules import ObjectType, make_executable_schema


class Query(ObjectType):
    __schema__ = gql(
        """
        type Query {
            message: String!
            year: Int!
        }
        """
    )

    def resolve_message(*_):
        return "Hello world!"

    def resolve_year(*_):
        return date.today().year


schema = make_executable_schema(Query)
app = GraphQL(schema=schema, debug=True)
```


### Dependency injection

If `__schema__` string contains other type, its definition should be provided via `__requires__` attribute:

```python
from typing import List, Optional

from ariadne.asgi import GraphQL, gql
from ariadne_graphql_modules import ObjectType, make_executable_schema

from my_app.users import User, get_user, get_last_users


class UserType(ObjectType):
    __schema__ = gql(
        """
        type User {
            id: ID!
            name: String!
            email: String
        }
        """
    )

    def resolve_email(user: User, info):
        if info.context["is_admin"]:
            return user.email

        return None


class UsersQueries(ObjectType):
    __schema__ = gql(
        """
        type Query {
            user(id: ID!): User
            users: [User!]!
        }
        """
    )
    __requires__ = [UserType]

    def resolve_user(*_, id: string) -> Optional[User]:
        return get_user(id=id)

    def resolve_users(*_, id: string) -> List[User]:
        return get_last_users()


# UsersQueries already knows about `UserType` so it can be omitted
# in make_executable_schema arguments
schema = make_executable_schema(UsersQueries)
app = GraphQL(schema=schema, debug=True)
```


#### Deferred dependencies

Optionally dependencies can be declared as deferred so they can be provided directly to `make_executable_schema`:

```python
from typing import List, Optional

from ariadne.asgi import GraphQL, gql
from ariadne_graphql_modules import DeferredType, ObjectType, make_executable_schema

from my_app.users import User, get_user, get_last_users


class UserType(ObjectType):
    __schema__ = gql(
        """
        type User {
            id: ID!
            name: String!
            email: String
        }
        """
    )

    def resolve_email(user: User, info):
        if info.context["is_admin"]:
            return user.email

        return None


class UsersQueries(ObjectType):
    __schema__ = gql(
        """
        type Query {
            user(id: ID!): User
            users: [User!]!
        }
        """
    )
    __requires__ = [DeferredType("User")]

    def resolve_user(*_, id: string) -> Optional[User]:
        return get_user(id=id)

    def resolve_users(*_, id: string) -> List[User]:
        return get_last_users()


schema = make_executable_schema(UserType, UsersQueries)
app = GraphQL(schema=schema, debug=True)
```


### Automatic case convertion between `python_world` and `clientWorld`

#### Resolving fields values

Use `__aliases__ = convert_case` to automatically set aliases for fields that convert case

```python
from ariadne.asgi import gql
from ariadne_graphql_modules import ObjectType, convert_case


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
from ariadne.asgi import gql
from ariadne_graphql_modules import MutationType, convert_case

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
from ariadne.asgi import gql
from ariadne_graphql_modules import InputType, MutationType, convert_case

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

    async def resolve_mutation(*_, input: dict):
        user = await create_user(
            full_name=input["full_name"],
            email=input["email"],
        )
        return bool(user)
```


### Roots merging

`Query`, `Mutation` and `Subscription` types are automatically merged into one by `make_executable_schema`:

```python
from datetime import date

from ariadne.asgi import GraphQL, gql
from ariadne_graphql_modules import ObjectType, make_executable_schema


class YearQuery(ObjectType):
    __schema__ = gql(
        """
        type Query {
            year: Int!
        }
        """
    )

    def resolve_year(*_):
        return date.today().year


class MessageQuery(ObjectType):
    __schema__ = gql(
        """
        type Query {
            message: String!
        }
        """
    )

    def resolve_message(*_):
        return "Hello world!"


schema = make_executable_schema(YearQuery, MessageQuery)
app = GraphQL(schema=schema, debug=True)
```

Final schema will contain single `Query` type thats result of merged tupes:

```graphql
type Query {
    message: String!
    year: Int!
}
```

Fields on final type will be ordered alphabetically.


## Contributing

We are welcoming contributions to Ariadne! If you've found a bug or issue, feel free to use [GitHub issues](https://github.com/mirumee/ariadne/issues). If you have any questions or feedback, don't hesitate to catch us on [GitHub discussions](https://github.com/mirumee/ariadne/discussions/).

For guidance and instructions, please see [CONTRIBUTING.md](CONTRIBUTING.md).

Website and the docs have their own GitHub repository: [mirumee/ariadne-website](https://github.com/mirumee/ariadne-website)

Also make sure you follow [@AriadneGraphQL](https://twitter.com/AriadneGraphQL) on Twitter for latest updates, news and random musings!

**Crafted with ❤️ by [Mirumee Software](http://mirumee.com)**
hello@mirumee.com

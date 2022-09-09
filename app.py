from ariadne import (
    QueryType, 
    gql,
)
from ariadne.asgi import GraphQL
from ariadne_graphql_modules import ObjectType, make_executable_schema


class RandomQueries(ObjectType):
    __schema__ = gql(
        """
        type Query {
            random: Int!
        }
        """
    )

    @staticmethod
    def resolve_random(root, info):
        return 6 # perfectly random number from dice roll


class UserType(ObjectType):
    __schema__ = gql(
        """
        type User {
            id: ID!
            name: String!
            score: Int!
        }
        """
    )

    @staticmethod
    def resolve_score(user, info):
        return user['id'] * 4


class UserQueries(ObjectType):
    __schema__ = gql(
        """
        type Query {
            users: [User!]!
        }
        """
    )
    __requires__ = [UserType]

    @staticmethod
    def resolve_users(root, info):
        return [
            {"id": 1, "name": "Bob"},
            {"id": 2, "name": "Alice"},
        ]



schema = make_executable_schema(
    RandomQueries, UserQueries,
)


app = GraphQL(schema)
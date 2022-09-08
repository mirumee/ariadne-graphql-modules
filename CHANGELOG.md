# CHANGELOG

## 0.6.0 (2022-09-08)

- Added support for `__args__ = convert_case` for `MutationType`.
- Changed `convert_case` to be less magic in its behavior.


## 0.5.0 (2022-07-03)

- Implement missing logic for `ObjectType.__fields_args__`


## 0.4.0 (2022-05-04)

- Split logic from `BaseType` into `DefinitionType` and `BindableType`.
- Add `CollectionType` utility type for gathering types into single type.


## 0.3.0 (2022-04-25)

- Fix "dependency required" error raised for GraphQL `Float` scalar type.

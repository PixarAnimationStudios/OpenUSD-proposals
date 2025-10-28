# Easier Multiple Apply Schemas

I would like to propose adding an (optional) field in the `customData` of a multiple apply schema definition that would
declare a default name.

This would reduce the friction of using multiple-apply schemas that have a recommended default name to use, such as the
accessibility schema.

## Problem Statement

Today, multiple apply schemas require an explicit name to be passed to their methods, even if the schema expects one
name to be used most commonly.

This then has some knock on effects:

* Schema authors need to define a new token explicitly
* Schema authors need to create convenience methods which may vary between schemas, and require custom binding.

## Proposal

Given a multiple apply schema, I propose adding an optional token called `defaultName`.

```
class "SampleAPI" 
(
    inherits = </APISchemaBase>
    doc = "My sample schema API"
    customData = {
        string apiSchemaType = "multipleApply"
        token defaultName = "foo"
"""
    }
)
{
}
```

I propose that `usdGenSchema.py` read this optional attribute and do the following:

1. Automatically creates the token if it doesn't exist already.
2. Set default parameter values for the name attribute

   e.g

    ```cpp
    Get(const UsdPrim &prim, const TfToken &name);
    ```

   would turn into

    ```
    Get(const UsdPrim &prim, const TfToken &name=TargetTokens->defaultName);
    ```

3. It should also document the default name in a standardized way in documentation.

This would mean that schema creators have less boilerplate to provide, there is less variance between each schema and it
naturally guides schema users to the right path.

## Risks and Alternate Solutions

This proposal should be very low risk.
The only issues I can think of are:

* if the header is somehow out of sync with the schema after someone changes the name. But that would be indicative of
  bigger problems.
* multiple-apply schemas without default names will stick out, but no more than they currently do. They might just have
  less company.

I also cannot think of alternate solutions beyond alternate field names.


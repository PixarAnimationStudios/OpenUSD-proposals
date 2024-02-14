# Contents
  - [USD Validation Framework](#usd-validation-framework)
  - [TL;DR](#story-in-a-nutsehll-tldr)
  - [Core Validation Framework](#core-validation-framework)
    - [Registration Infrastructure](#registration-infrastructure)
      - [UsdValidationRegistry](#usdvalidationregistry)
      - [UsdValidators](#usdvalidators)
        - [UsdValidatorMetadata](#usdvalidatormetadata)
        - [UsdValidator](#usdvalidator)
        - [UsdSchemaTypeValidator](#usdschematypevalidator)
        - [UsdValidatorSuite](#usdvalidatorsuite)
      - [Testing Task Functions](#testing-task-functions)
        - [LayerTestingTask](#layertestingtask)
        - [StageTestingTask](#stagetestingtask)
        - [PrimTestingTask](#primtestingtask)
        - [Validating Core USD Behaviors](#validating-core-usd-behaviors)
      - [Keyword Tagging for Tests](#keyword-tagging-for-tests)
      - [Codeless Schemas](#will-codeless-schemas-just-work)
    - [Running Infrastructure](#running-infrastructure)
      - [UsdValidationContext](#usdvalidationcontext)
      - [Running Tests](#running-tests)
      - [UsdValidationError](#usdvalidationerror)
      - [UsdValidationFixer](#usdvalidationfixer)
  - [Additional Supported Work](#additional-supported-work)
  - [Future Work](#future-work)
  - [Risks](#risks)
  - [Rollout Plan](#rollout-plan)
    
# USD Validation Framework
The proposal describes the need for a core USD validation framework, with some 
background and an implementation plan for the same.

## Why have Validation in USD?
USD is very flexible and every site/studio including Pixar using USD can
establish their own rules and patterns to cater to a custom pipeline. At the
same time USD itself defines certain rules, like the ones defined in the core
schema or defined in the library itself (example model hierarchy rules). It is
important to validate these rules so as to give higher confidence to the
downstream department or external customer that the asset being consumed is free
of any rule violations.

Having a framework which can be adopted per site via plugins for validators can
provide greater flexibility for validating assets.

Such a validation framework can also be used as a first line of defense when
debugging a broken asset.

## Why a new framework?
Usd's compliance checker and utilities like usdchecker have served us well, but
lack some core functionalities like providing a robust framework and APIs to
extend validators for all core usd schemas or for clients to provide validators 
for their pipeline needs. 

`UsdUtilsComplianceChecker` and `usdchecker` also do not provide any insights on
composition errors or value resolution errors. Currently these are reported as
warnings internally when composing a stage or when explicitly evaluating a value
of an attribute.

There is no task parallelism, as the current implementation is all in python,
which is a must for a testing infrastructure where hundreds of tests are
executed on a specific asset to provide a fast and robust validation.

# Core Requirements
Following are some of the core requirements for a new Validation Framework.

 - C++ based core framework, with appropriate python bindings. 
 - Ability for core schema developers to write and register core schema rules as
   validators.
 - Plugin based workflow to add new validators. 
 - Ability to provide configurability of tests to be executed for validation,
   per-site, per-application and for varying sets of Stages. 
 - Task parallelism to execute validators in parallel.

Core public APIs are being designed to answer questions like: 
 - Should schema authors provide tests governing the schema rules? 
 - What does it mean to validate a layer? 
 - What does it mean to validate a stage? 
 - What does it mean to validate a prim? 
 - What tests to run for a specific scenario? 
   - Should clients be able to filter out tests based on certain criteria /
     keywords / types, cache these tests and run. 
   - Should a validation framework only run a user provided list of validators?
     Or should it also do more than that, by providing insight on what's
     fundamentally incorrect about an asset, whether its properties are
     conforming to a spec or have errors which even though not explicitly
     checked must also be reported - for example composition errors? 
 - Ability to run adhoc validators on an asset of a subset (prims) of an asset. 
   - A TD is working in an environment and wants to verify if a certain scenario
     is valid, but doesn't necessarily want to register a test for it. Can the
     TD run an adhoc test on a prim/stage/layer. 
 - Ability for clients to make a suite of validators, which can optionally
   bundle tests from various plugins in order to validate the concept / feature
   / specification.

# Story in a nutsehll (TL;DR)
USD core will provide a registry of validators for each schema domain and
possibly some schema types (Typed and APISchema) catering to rules for each
schema domain and schema types respectively. Clients of USD will also be able to
provide their own validators, registered via plugin mechanism, catering to their
workflow/pipelines.

Every validator can also be associated with a set of keywords which can then be
used for filtering along with schema types. Example: a test can be tagged with a
schema domain it caters to, or a test specific to a custom render can be tagged
appropriately with an appropriate keyword.

USD Core validators will also be implemented which along with validators for
core usd schemas and specification, will also validate core usd behaviors like
reporting any composition errors etc.

Validation logic for each test is implemented via `LayerTestingTask`,
`StageTestingTask` or a `PrimTestingTask`. A validator can also be defined as a
suite of prefiltered sets of tests from possible varied plugins which the
clients can distribute in their plugin. For example, the hdprman plugin can
provide a `UsdValidatorSuite`, which will include a prefiltered set of
validators (Core USD rules + renderman specific tests). Such a suite of
validators can help answer the question - Is an asset "renderable" using hdprman
or not?

For running validators, client applications can create a `UsdValidationContext`.
A validation context can be created either by providing a set of schemaTypes, a
set of keywords or a prefiltered set of tests. This is also where the specified
plugins providing these tests will get loaded. Note that filtered out tests will
also contain tests from parent schemaType. For example, if a context is created
for `UsdGeomSphere`, tests from all types which Sphere inherits (like Imageable
etc) will also be included. 

Clients can run these tests via the `UsdValidationContext` instance they
created. Errors from these runs are stored in this instance, which can then be
appropriately reported by the client application. Test writers can optionally
provide a set of possible fixers, which can be appropriately be invoked from the
Error instance to be fixed.

# Core Validation Framework
The Framework is divided into 2 infrastructure blocks
 - Registration Infrastructure
 - Running Infrastructure

## Registration Infrastructure

### UsdValidationRegistry
`UsdValidationRegistry` holds a registry of validators, instantiated when the
corresponding plugin gets loaded. The implementation here might maintain a few
multimaps to cache tests per plugin, tests per keyword and tests per schemaType.

`UsdValidationRegistry` will subscribeTo and cause appropriate
`TF_REGISTRY_FUNCTION` to be run lazily when test plugins are loaded.

The registry will provide appropriate helper APIs in order for clients to
inspect what tests are provided by each plugin, some of these could look like:

``` cpp
/// Returns a vector of all available tests by inspecting plugInfo for all 
/// plugins.
///
std::vector<UsdValidatorMetadata>
UsdValidationRegistry::GetAllTests()

/// Returns a vector of all tests satisfying the list of keywords by inspecting
/// plugInfo for all plugins.
///
std::vector<UsdValidatorMetadata>
UsdValidationRegistry::GetAllTests(std::vector<TfToken> keywords)

/// Returns a vector of all tests satisfying the list of schemaTypes by
/// inspecting plugInfo for all plugins.
///
std::vector<UsdValidatorMetadata>
UsdValidationRegistry::GetAllTests(std::vector<TfToken> schemaTypes)
```

Clients can use the above-mentioned APIs to populate a set of tests they want to
use for their `UsdValidationContext` or to instantiate an `UsdValidatorSuite`,
which comprises these filtered out tests.

Validators are added under the "Validators" named dictionary in plugInfo.json.
All the "Validators" in a plugin can have a common set of keywords, keyed by
["Validators"]["keywords"] in the plugInfo.json. Each entry in the "Validators"
dictionary other than "keywords" then represents a single TestName.

Each test can have the following metadata:
 1. **"doc"**: A required field for all tests, and provides the documentation
    for each test. This can help UI designers provide a tool tip for each test.
 2. **"keywords"**: Along with keywords inherited from plugin's validators
    keywords, each test can have optional keywords specific to that test.
 3. **"schemaType"**: An optional field telling to what schemaTypes this test is
    applicable to. This information is then used to run this test on only prims
    of the specified type.
 4. **"isSuite"**: An optional field telling if this test represents a
    collection of other tests. Clients can use this to bundle all sets of tests
    which are important to their needs. For example hdprman, can provide a test
    suite which encompasses all core usd validators and another set of
    validation rules specific for renderman needs.

Following is the template for plugInfo with appropriate comments explaining each
metadata field: 
```
"Validators": 
{
    # optional keywords which are applicable to all tests in this plugin
    "keyword": []

    # dictionary of metadata values keyed on a named test.
    "TestName1":
    {
        # Required documentation for this "TestName1" test
        "doc": ""

        # Optional metadata field, list of schemaTypes this "TestName1" test is 
        # applicable to.
        "schemaType": []

        # Optional keywords specific to this "TestName1" test
        "keywords": []

        # Optional metadata field, shows if this "TestName1" test represents a 
        # collection of other tests.
        "isSuite":
    },

    # dictionary of metadata values keyed on a named test.
    "TestName2": 
    { 
        "doc": ....
        ....
        ....
    }
....
....
}
```

Example of plugInfo.json showing test metadata:

```
{
    "Plugins": [
    {
        "Info": {
            "Name": "usdShade"
            "LibraryPath": "@PLUG_INFO_LIBRARY_PATH",
        },
        ....
        ....
        ....
        "Validators": {
            "keywords" : ["UsdCoreValidators"]
            "ShaderEncapsulationTest": {
                "schemaType": "Shader"
                "doc": "Test to make sure Shader prims are encapsulated 
                         under a Material prim's scope"
            },
            "CollectionBasedBindingRelTargetTest": {
                "schemaType": "MaterialBindingAPI"
                "doc": "A test to make sure a collection based binding
                         relationship, if present must have exactly 2
                         targets, one for collectionPath and other for
                         UsdShadeMaterial"
            },
            "SomeOtherGenericUsdShadeTest": {
                "doc": "Testing some generic UsdShade inter schema rule."
            },
            ...
            ...
       }
    ]
}

```

Test writers will be responsible to fill in appropriate metadata for their tests
in the plugInfo, and test writers will also need to instantiate their tests in
`TF_REGISTRY_FUNCTION(UsdValidationRegistry)`.

Example of `TF_REGISTRY_FUNCTION` usage to instantiate the 2 tests shown above:

<a name="Example1"></a>
``` cpp
TF_REGISTRY_FUNCTION(UsdValidationRegistry)
{
    /// Add a SchemaTypeValidator which has its testing functionality 
    /// implemented in "GetShaderEncapsulationTestImpl()"
    UsdValidationRegistry::GetInstance().AddSchemaTypeValidator(
        "ShaderEncapsulationTest", GetShaderEncapsulationTestImpl());

    /// Add a CollectionBasedBindingRelTargetTest which has its testing
    /// functionality implemented in "GetCollectionBindingTestImpl()"
    UsdValidationRegistry::GetInstance().AddSchemaTypeValidator(
        "CollectionBasedBindingRelTargetTest", GetCollectionBindingTestImpl());

    /// Add a SomeOtherGenericUsdShadeTest which has its testing
    /// functionality implemented in "Func1StageTestingTaskImpl()"-which is a
    /// StageTestingTask.
    /// More about StageTestingTask, LayerTestingTask and PrimTestingTask
    /// later.
    UsdValidationRegistry::GetInstance().AddValidator(
        "SomeOtherGenericUsdShadeTest", 
        Func1StageTestingTaskImpl() /*StageTestingTask*/ 
    );
}
```
**Note** about test names: Since plugin names are guaranteed to be unique in the
entire USD library, and each plugin can only have unique test names,
ValidatorMetadata will store a test name as a _"pluginName:testName"_ where
pluginName is the name of the plugin the test belongs to and testName
corresponds to the entry of the test in the plugInfo.json.

Also note that when registering of tests, a coding error could be reported if
all the tests mentioned in the plugInfo are not not registered when the plugin
gets loaded, by appropriately providing an initialization for each test in the
`TF_REGISTRY_FUNCTION`.

Having test names and each test's doc in the plugInfo will help the interface
provide info about what tests it has, using appropriate docs.

### UsdValidators

#### UsdValidatorMetadata
As mentioned above each test is represented with some metadata in the 
plugInfo.json corresponding to the test's plugin. This structure holds onto 
these metadata values. Metadata for each test can be extracted using the APIs in 
`UsdValidationRegistry`. A `UsdValidator` will hold onto its corresponding 
metadata, when it gets instantiated during its plugin load time.

``` cpp
struct ValidatorMetadata
{
    /// "pluginName:testName" corresponding to the entry in plugInfo.json
    TfToken name;
    
    /// list of keywords extracted for this test from the plugInfo.json
    std::vector<TfToken> keywords;

    /// doc string extracted from plugInfo.json
    std::string docs;

    /// list of schemaType names this test applies to, extratced from
    /// plugInfo.json
    std::vector<TfToken> schemaType;

    /// whether this test represents a test suite or not
    bool isSuite;
};
```

#### UsdValidator
`UsdValidator` is a class describing a single test. An instance of
`UsdValidator` is created when plugins are loaded and tests are registered and
cached in the `UsdValidationRegistry`.

`UsdValidator` consists of any one of the 3 testing tasks:
`LayerTestingTask`, `StageTestingTask` or `PrimTestingTask`, which correspond to
testing the given `SdfLayer`, an entire `UsdStage` or `UsdPrim` respectively.
A [previous example](#Example1) shows how a client will be able to instantiate
and add a `UsdValidator` when registering a test.

A `UsdValidator` class might look as:

``` cpp
class Validator
{
private:
    ValidatorMetadata _testMetadata;
    LayerTestingTaskFn _layerTestingTask;
    StageTestingTaskFn _stageTestingTask;
    PrimTestingTaskFn _primTestingTaskFn;

    std::vector<Fixer> _suggestedFixers; // Refer Fixers below
public:
    Validator(const ValidatorMetadata&, const LayerTestingTaskFn);
    Validator(const ValidatorMetadata&, const StageTestingTaskFn);
    Validator(const ValidatorMetadata&, const PrimTestingTaskFn);
    Validator(const ValidatorMetadata&, const std::vector<Validator>);

    /// various accessor and helper APIs ///
};
```

#### UsdSchemaTypeValidator
`UsdSchemaTypeValidator` extends `UsdValidator` and is only applicable for
validators which are associated with a schemaType metadata. Because of this
association these validators must only operate on a given prim, and hence
`UsdSchemaTypeValidator` only provides access to `PrimTestingTaskFn`.

A [previous example](#Example1) (test for `UsdShadeShader` and
`UsdShadeMaterialBindingAPI` schemaTypes) shows how a client will be able to
instantiate and add a `UsdSchemaTypeValidator` when registering a test.

`UsdSchemaTypeValidator` class might look like this:

``` cpp
class SchemaTypeValidator : public Validator
{
public:
    SchemaTypeValidator(const ValidatorMetadata& testMadata, 
        const PrimTestingTaskFn primTestingTask) : TestingTaskFn(testMetadata, 
            primTestingTask), _layerTestingTask(nullptr),
            _stageTestingTask(nullptr) {}

    /// other accessor and helper APIs ///
};
```

#### UsdValidatorSuite
`UsdValidatorSuite` also inherits from `UsdValidator` but instead of providing
any TestingTaskFn it acts like a suite for a collection of tests, which clients
can use to bundle all tests relevant to test their concepts (example: a
renderer: CoreUSD tests + renderer specific tests, a physics sim: CoreUSD tests
and physics sim specific tests, etc.)

An example of how a client can instantiate a `UsdValidatorSuite` during
registration:

```
{
    "Plugins": [
    {
        "Info": {
            "Name": "myAwesomeRenderer"
            "LibraryPath": "@PLUG_INFO_LIBRARY_PATH",
        },
        ....
        ....
        ....
        "Validators": {
            "keywords" : ["MyAwesomeRendererTests"]
            "SpecificTestForMyAwesomeRendere": {
                 "doc": "This test checks for a specific requirement for a
                 stage to be valid to be renderable with MyAwesomeRenderer"
            },
            "MyAwesomeRendererTestSuite": {
                "doc": "This test is a collection of all tests which must be
                satisfied for an asset to be deemed renderable using
                MyAwesomeRenderer"
            },
            ...
            ...
       }
    ]
}

```
``` cpp
TF_REGISTRY_FUNCTION(UsdValidationRegistry)
{
    std::vector<UsdValidator> allTestForMyAwesomeRenderer;

    /// Gather tests to be part of this suite from the Registry, and if not 
    /// cached, let the registry load the plugin and get individual 
    /// Validators.
    auto allCoreUsdTestsMetadata = UsdValidationRegistry::GetAllTests(
            {"UsdCoreValidators"} /*keywords*/ );
    /// loop through these and Get/Load UsdValidator corresponding to 
    /// "UsdCoreValidators" keyword and fill "allTestForMyAwesomeRenderer" 
    /// vector.

    /// create any specific not-suite UsdValidator instance and add to 
    /// UsdValidationRegistry.
    UsdValidationRegistry::GetInstance().AddValidator(
        "SpecificTestForMyAwesomeRenderer" /*keywords*/, 
        SpecificStageTestingTaskImpl() /*StageTestingTask*/ 
    );
    allTestForMyAwesomeRenderer.append(
        UsdValidationRegistry::GetOrLoadTest(
            "myAwesomeRenderer:SpecificTestForMyAwesomeRenderer"));

    /// once done, use allTestForMyAwesomeRenderer to create an instance of 
    /// UsdValidatorSuite
    UsdValidationRegiatry::GetInstance().AddValidatorSuite(
        "MyAwesomeRendererTests", allTestsForMyAwesomeRenderer);
}
```

`UsdValidatorSuite` class might look like this:
``` cpp
class ValidatorSuite : public Validator
{
private:
    std::vector<Validator> _containedTests;
public:
    ValidatorSuite(const ValidatorMetadata &metadata, 
        const std::vector<Validator> containedTests) : 
            _testMetadata(metadata), _containedTests(containedTests),
            _layerTestingTask(nullptr), _stageTestingTask(nullptr), 
            _primTestingTask(nullptr) {}

    // Base class will provide a default implementation for this which returns
    // an empty vector;
    std::vector<Validator> GetContainedTests() const override;

    /// other access or helper APIs //
};
```

#### Testing Task Functions
A testing task function holds the implementation of the actual testing rules
written by a test writer. A validation test task method can work off a
`SdfLayer`, `UsdStage` or a `UsdPrim`, and the test writer will appropriately
provide implementation for one or all of the following TestTask functions:

 1. `LayerTestTaskFn`: `std::function<ValidationError(const SdfLayer& layer, std::optional<TimeCode>& timeCode)>`
 2. `StageTestTaskFn`: `std::function<ValidationError(const UsdStage& usdStage, std::optional<TimeCode>& timeCode)>`
 3. `PrimTestTaskFn`: `std::function<ValidationError(const UsdPrim& usdPrim, std::optional<TimeCode>& timeCode)>`

These methods will act as appropriate callbacks when running the test. Also note
that for test writers providing callables in python, appropriate wrappers will
convert these to `std::functions`. 

Having a callback approach instead of a polymorphic approach (derived test
classes implementing TestLayer, TestStage, TestPrim methods) helps with python
wrapping implementations.

TestingTask implementation will return an instance of `UsdValidationError`,
which will get stored in the `UsdValidationContext` instance responsible for
running a set of tests. In case of a passing (not failing) test a default
`UsdValidationError` is reported, otherwise an appropriate `UsdValidationError`
is constructed and returned. It is the responsibility of the test writer to
provide appropriate error information when implementing the testing
functionality.

Test writers also have an option of using the optional timecode parameter, which
can be used to evaluate properties at specific timecode, etc.

Implementation Note:
While implementing these concepts, we might consider a generic TestingTask
template, deducing StageTestingTask, LayerTestingTask or PrimTestingTask
appropriately, even though these concepts are explicitly separated out in the
proposal.

Following are some examples of Layer, Stage or a Prim test task functions
showing the usage of testing method, keywords and error reporting.

##### LayerTestingTask
An example of a `LayerTestTaskFn` usage which a client can use to construct a
`UsdValidator`:

``` cpp
/// A testing task checking the validity of a layer's file format.
LayerTestTaskFn supportedFileFormatTestFn = [](const SdfLayer& layer,
    std::optional<TimeCode>& timeCode) -> ValidationError {
        const TfTokenVector allowedFormats = {'usd', 'usda', 'usdc', 'usdz'};
        const TfToken& formatId = layer.GetFileFormat()->GetFormatId();
        if (allowedFormats.begin(), allowedFormats.end(), formatId) ==
            allowedFormats.end()) {
                return ValidationError(
                    ValidationErrorType.Error /*type*/,
                    this /*pointer to failing test*/, 
                    ErrorSite(layer, UsdStage(), SdfPath("") /*path*/),
                    "Specified file format is not allowed" /*error message*/);
        }
        return ValidationError();
    };
```

##### StageTestingTask:
An example of a `StageTestTaskFn` usage which a client can use to construct a
`UsdValidator`:

``` cpp
/// A testing task to make sure stage has the correct up axis for arkit assets.

StageTestTaskFn arkitUpAxisStageMetadataTestFn = [](const UsdStage& usdStage,
    std::optional<TimeCode>& timeCode) -> ValidationError {
        if (usdStage.HasAuthoredMetadata(UsdGeomTokens->upAxis)) {
            const TfToken& upAxis = UsdGeomGetStageUpAxis(usdStage);
            if (upAxis != UsdGeomTokens->y) {
                return ValidationError(
                    ValidationErrorType.Error /*type*/,
                    this /*pointer to failing test*/, 
                    ErrorSite(SdfLayer(), usdStage/*stage*/, 
                        SdfPath("") /*path*/),
                    "Incorrect up axis...." /*error message*/);
            } else {
                return ValidationError();
            }
        } else {
            return ValidationError(
                ValidationErrorType.Error /*type*/,
                this /*pointer to failing test*/, 
                ErrorSite(SdfLayer(), usdStage/*stage*/, SdfPath("") /*path*/),
                "No up axis...." /*error message*/);
        }
    };

```

##### PrimTestingTask
An example of a `PrimTestTaskFn` usage which a client can use to construct a
`UsdValidator`:

``` cpp
/// A testing task to make sure a prim having material binding relationship has
/// MaterialBindingAPI applied to it.

/// NOTE: This specific test will generically be handled by a core generic
/// APISchema checker, which ensures appropriate API Schemas are applied.

PrimTestTaskFn materialBindingAPITest = [](const UsdPrim& usdPrim,
    std::optional<TimeCode>& timeCode) -> ValidationError {
        hasMaterialBindings = [&]() {
            for (auto rel : prim.GetRelationships()) {
                if (TfStringStartsWith(rel.GetName(),
                    UsdShadeTokens->MaterialBindingAPI)) {
                        return true;
                }
            }
            return false;
        }();

       if (hasMaterialBindings and !prim.HasAPI<UsdShadeMaterialBindingAPI()) {
           return ValidationError(
                    ValidationErrorType.Error /*type*/,
                    this /*pointer to failing test*/, 
                    ErrorSite(SdfLayer(), 
                              prim.GetStage() /*stage*/, 
                              prim.GetPath() /*path*/),
                    "MaterialBindingAPI not applied ......" /*error message*/);
       }
       return ValidationError();
    };
   
    [](const ValidationError& e, std::optional<TimeCode>& timeCode) -> bool {
        UsdPrim prim = e.GetErrorSite().GetUsdStage().GetPrimAtPath(
                           e.GetErrorSite().GetPath());
        return UsdShadeMaterialBindingAPI::Apply(prim);
    } /*fixer function*/
);
```

An example of a `PrimTestTaskFn` usage which a client can use to construct a
`UsdSchemaTypeValidator`:

``` cpp
/// A Validation test to make sure a diskLight's intensity is below 10 at any
/// given timecode as a requirement for a specific show. Such a testing task
/// could be used to create a UsdSchemaTypeValidator, where schemaType is
/// set as DiskLight. 

PrimTestTaskFn diskLightIntensityTest = [](const UsdPrim& usdPrim,
    std::optional<TimeCode>& timeCode) -> ValidationError {
        /// check usdPrim's type being a disk light, return no error if not.
        /// get intensity property from the prim
        /// evaluate intensity at given timecode and compare it with 10.
        /// if < 10, return no error
        /// else return error.
    };

```

##### Validating Core USD Behaviors
`UsdUtilsComplianceChecker` never reported on any core usd errors coming from
composition or any internal USD implementation behaviors. We plan to provide a
set of core usd validator plugins which will report all of these internal
malformed USD behaviors. 

Following shows an example of registration of a couple of tests,
"CompositionErrorTest" and "ExpressionSyntaxErrorTest" both of which have a
"UsdCoreValidators" keyword set.

```
{
    "Plugins": [
    {
        "Info": {
            "Name": "usd"
            "LibraryPath": "@PLUG_INFO_LIBRARY_PATH",
        },
        ....
        ....
        ....
        "Validators": {
            "keywords" : ["UsdCoreValidators"]
            "CompositionErrorTest": {
                "doc": "Test to report composition errors."
            },
            "ExpressionSyntaxErrorTest": {
                "doc": "Test to report syntax errors in expression
                        evaluations."
        },
        ...
        ...
       }
    ]
}

```

``` cpp
TF_REGISTRY_FUNCTION(UsdValidationRegistry)
{
    /// Add a validator which has its testing functionality implemented by
    /// compositionErrorTestFn
    StageTestTaskFn compositionErrorTestFn = [](const UsdStage& usdStage,
        std::optional<TimeCode>& timeCode) -> ValidationError {
        /// Implementation to extract composition errors from pcpLayerStack
        /// and all prim indices in the stage.
        /// if composition errors are reported, Wrap these appropriately by
        /// a ValidationError and return.
    };
    UsdValidationRegistry::GetInstance().AddValidator (
        "CompositionErrorTest", compositionErrorTestFn);

    /// Add a validator which has its testing functionality implemented by
    /// expressionSyntaxErrorTestFn
    StageTestTaskFn expressionSyntaxErrorTestFn = [](const UsdStage& usdStage,
        std::optional<TimeCode>& timeCode) -> ValidationError {
        /// For all properties providing asset paths from all prims in the
        /// stage, check if the expression is free of any syntax errors
        /// using the SdfVariableExpression APIs. 
        /// If any errors are reported on these asset paths, wrap these
        /// under a ValidationError and return.
    };
    UsdValidationRegistry::GetInstance().AddValidator(
        "ExpressionSyntaxErrorTest", expressionSyntaxErrorTestFn);
```

Other core internal error handling functionalities will also be implemented,
such as rule to find missing Applied Schemas.

#### Keyword Tagging for Tests
As mentioned above, a test writer can provide tagging for each validator. These
tags are called as Keywords in this document. Notice that some of the examples
in `UsdValidator` section above have keywords specified.

#### Will codeless schemas just work?
Since the registration of tests is not tied to any generated code of a usd
schema, test can be written in a plugin for any codeless schema. Though test
writers when writing any test for a codeless schema will have to make sure to
use generic USD APIs, since codeless schemas do not provide any APIs of their
own.

## Running Infrastructure
The other part of this infrastructure is running tests and reporting of errors
or warnings. As a client using the validation framework, it is important to 
control which tests will be run and group these accordingly. 

Also do note that when test execution is triggered, these testing tasks will be
executed in parallel.

### UsdValidationContext
`UsdValidationContext` provides an interface to cache a filtered set of unique
tests which can be run to validate a layer, stage or a set of prims. It will
also hold the set of errors which will be generated as part of running these
tests.

In addition to keeping a reference of filtered tests to run, a validation
context could be provided with adhoc tests (which a user or a technical artist
writing a test in the python interpreter of an app can use). This concept can be
used in a scenario where a user wants to make sure a set of operations / asset
constructs doesn't violate any specific rule, before actually committing to
things.

This is also where plugin metadata will be queried to determine if a test's
plugin is required to be loaded, if not loaded and cached in the
`UsdValidationTestRegistry` already.

Possible available constructor overloads, giving clients an option to construct
an instance of `UsdValidationContext` by providing a set of test keywords, or by
providing a set of SchemaTypes, or even by providing a prefiltered set of tests.

``` cpp
/// Create a ValidationContext by getting all tests from all specified keywords
ValidationContext(const TfTokenVector& testKeywords);

/// Create a ValidationContext by getting all tests from all specified
/// schemaTypes
ValidationContext(const std::vector<TfType>& schemaTypes);

/// Create a ValidationContext from a given list of UsdValidatorMetadata
/// Clients can use the mentioned UsdValidationRegistry APIs to filter and
/// construct the list as per their needs.
ValidationContext(const std::vector<UsdValidatorMetadata>& testsMetadata);

/// A validation context created with an explicit set of dynamically created
/// validators. Maybe in the client application's python interpretor and
/// have no association to a plugin.
ValidationContext(const std::vector<UsdValidator> adhocTests);
```

`UsdValidationContext` will also provide the following APIs:
 - APIs to run the filtered out tests on a stage, layer or a set of prims.
 - API to set a timecode. For tests which are evaluating property values.
   TimeCode::Default is used if not set, when running the test timecode can then
   be passed to the Testing functions. 
 - APIs for reporting of these errors

### Running Tests
In order to run a testing task, `UsdValidationContext` needs to determine what
testing tasks need to be run and on what! The testing tasks have already been
determined before the tests are run, based on the tests cached with the instance
of the validation context when it was created.

It's trivial to run UsdValidators which have a `StageTestingTask` or a
`LayerTestingTask` as these won't require any stage traversal. But UsdValidators
having PrimTestingTasks will run on prims, which either are explicitly provided
or a `PrimRange` is constructed from a stage traversal.

For `UsdSchemaTypeValidator` which are defined for a specific schemaType, the
test needs to run only the specified schemaType prims (or prims which have the
schemaTypeAPI applied).

**Note:** Special implementation logic will need to be added to make sure
certain iterations of UsdValidators having `PrimTestingTask` can be interrupted
in order to not have these run on all prims when a specific condition is
satisfied. This may be achieved by returning Error having a specific property
which the traversal / task queueing code can inspect, to prune appropriate
testing tasks from the queue (or not enqueue respective new testing tasks).

The following is one way the `ValidationContext::RunTests` could be structured
to run filtered tests, such that appropriate stage traversal is done to get
`PrimRange` to run tests on:

```
// Add UsdValidator having a StageTestingTask to test running queue
For cached validators having StageTestingTask:
    AddTestTaskToQueue(validator.GetStageTestingTaskFn(stage,
        GetTimeCode());

// Add UsdValidator having a LayerTestingTask to test running queue
For cached validator having LayerTestingTask:
    if layerProvidedForTesting:
        AddTestTaskToQueue(validator.GetLayerTestingTaskFn(layer,
            GetTimeCode())
    else:
        AddTestTaskToQueue(validator.GetLayerTestingTaskFn(
            stage.GetRootLayer(), GetTimeCode())

primRange = Stage::Traverse()
For prim in primRange:
    for cached validators having PrimTestinTask:
        if (validator.HasSchemaTypeDefined() &&
            (prim.IsA(validators.GetSchemaType()) or
            (primValidator.schemaType.IsAPISchema() and
            prim.HasAPI(primValidator.schemaType))):
                if (validator.GetName() in not list of test to not be
                    enqueued further):
                AddTestTaskToQueue(validator.GetPrimTestingTask(
                    prim, GetTimeCode())
```

Additionally we can have overriding APIs which provide stage traversal
predicates, which can be used to get `PrimRange` to run the prim tests on.

These test runners will fill in the vector of errors held by the validation
context, which can then be queried using appropriate APIs on
`UsdValidationContext`.

### UsdValidationError
A validation error is returned when a validator fails. Test writers must provide
the following information when returning an error from a testing function.

 - **ErrorType**:
   Determines the severity of an error. Can have the following values: 
   - Error: A rule violation, which must be fixed in order to pass validation.
   - Warning: A situation which will not break the asset, but will be good for
     the artist/TD/content provider to fix.
   Internal core usd errors like composition errors or value resolution errors
   or expression syntax errors will be reported as `ErrorType::Error`, as these
   are actual asset breaking issues and must be fixed by the content creator.

 - **ErrorSite**: 
   A structure which defines where the error occurred so as to easily provide
   information about the error in the error message or to the fixer callback.
   The site could be a layer, stage or a prim path. Notice that these correspond
   to the testing callbacks. Appropriate APIs to access these sites will be
   provided.

 - **ErrorMessage**:
   The test writer is responsible for providing a detailed error message, so as
   to help the client with enough information to fix the violating rule,
   especially when a fixer method is not provided for the failing test.

A hash of these `ValidationError` properties can be together used as a
`ErrorID`, which the client application can use to determine if the
ValidationErrors are "fixed" in a subsequent iteration of running the tests.

`ValidationError` has a reference/pointer to the failing test, this is helpful
to find all fixers which might be provided for the failing test.

### UsdValidationFixer
Test writers have an option of providing optional multiple fixers when
registering a test. The reason a test can have multiple fixers is because
depending on the test, there could be possibly many ways a test can be fixed.
Example in case of a model hierarchy test failure, the fix could be to add an
appropriate kind metadata on the prim or on its parent prim.

A list of fixer instances can be created during registration of the test in the
appropriate `TF_REGISTRY_FUNCTION` and appropriately set while initializing a
`UsdValidator`.

A `UsdValidationFixer` class might look as:

``` cpp
using FixerImpFn = std::function<bool>(const ValidationError& e,
                       const UsdTimeCode& timeCode);
using FixerCanApplyFn = std::function<bool>(const ValidationError& e);
class UsdValidationFixer
{
private:
    std::string _name;
    
    /// shortDesciption will be helpful when enlisting a list of fixers in a UI
    std::string _shortDescription;
    
    /// longDescription will be helpful in a tool tip.
    std::string _longDescription;
    
    /// Actual implementation which authors the fix at the ErrorSite.
    /// Note that fix will be authored at the currently set EditTarget
    /// a timeCode must also be provided, to determine where the fix should be
    /// authored.
    FixerImpFn _fixerImp;
    
    /// A method which the test writer can provide which checks if a fix can be
    /// applied. It can check if there are permissions to author opinions at
    /// the current edit target, etc.
    FixerCanApplyFn _fixerCanApplyFn

public:
    bool CanApplyFix(const ValidationError& e);
    bool ApplyFix(const ValidationError& e, const UsdTimeCode& timeCode);

/* possible other helper APIs */
};
```

Example of a `FixerImpFn`:

``` cpp
/// Following fixer could be included with a test which checks if a
/// MaterialBindingAPI is applied or not on a prim:
FixerImpFn materialBindingAPIFixer = [](const UsdValidationError& e,
    const UsdTimeCode& timeCode) -> bool {
    UsdPrim prim = e.GetErrorSite().GetUsdStage().GetPrimAtPath(
        e.GetErrorSite().GetPath());
    return UsdShadeMaterialBindingAPI::Apply(prim);
}
```

Clients can use a few helper APIs on `UsdValidator` like `GetAllFixers()`,
`GetFixer(const std::string fixerName)` etc to retrieve a Fixer instance
associated with a given test. The client can then use the `UsdValidationFixer`
interface to see if a fix can be applied on an error and to apply the fix,
something along the following lines:

``` cpp
UsdValidatioError error = validationContextInstance.GetErrors()[0];
// Get all fixers for the error from its test
auto allFixers = error.GetTest().GetAllFixers();

// Get a specific fixer the client wants to apply
Fixer fix = error.GetTest().GetFix("fixerName")
if (fix.CanApplyFix(error)) {
    fix.ApplyFix(error);
}
```

**Note** that running of fixes is single threaded and must only be run after running
the tests.

## Additional Supported Work

### Core USD Schema Validators
We plan to provide core usd schemas validators registered as part of the library
itself. Each schema domain / schema type will be registered with a set of tests
which govern the rules for that concept.

This will encourage and allow schema writers to themselves control what
validation its clients should be validating for.

As part of this proposal, we plan to implement tests to achieve parity with the
current `UsdComplianceChecker` behavior in the new system.

### usdchecker rewrite
As part of this proposal, we plan to provide a complete rewrite of the
usdchecker utility in C++ to make use of the new Validation Framework and to
validate the set of tests available through current usdchecker.

usdchecker will instantiate a `UsdValidationContext`, using keywords or
schemaTypes if provided and run the tests, providing a log of the run, including
Errors and Warnings.

## Future Work
 - Extending tests for core schemas to provide better coverage of the testing
   infrastructure.
 - usdview hooks:
   General validation to run all registered validators. Widget based
   `UsdValidationContext` to limit validators pertaining to that widget.
   Example, a validationContext attached to the shader graph widget will only
   run usdShade related validation tasks.

## Risks
 - With deployment of the new framework, should we phase out the use of
   `UsdComplianceChecker` and old `usdchecker`? There are USD clients who are
   using and extending this system for their own purposes. We can discuss and
   see if their requirements are satisfied with the new framework and if so
   phase old systems out in a span of a couple of release cycles?

 - Fixer functionality and authoring on edit targets. It's possible a fixer
   might not fix the failing test, maybe because of lack of access to the edit
   target layer, or other reasons. It is also possible a fixer while fixing one
   test, causes another test to fail. We believe such a cyclic issue must be
   fixed by one of the test writers.

## Rollout Plan
 - Registration Framework
 - Running Framework
 - Implement rules to match current UsdUtilsCompliance checker scenarios
 - usdchecker rewrite to match current behavior
 - Framework for fixers will be implemented at the end.

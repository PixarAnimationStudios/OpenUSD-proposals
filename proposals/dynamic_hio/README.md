# Dynamic HIO Types

## Summary

This proposal suggests allowing for HIO plugins to register their supported extension list dynamically.

## Problem Statement

Today, we have two HIO plugins that can support numerous file types: `OpenImageIO` and `ImageIO`. However, the `PlugInfo.json` only supports a static list of extensions, meaning they're often limited to just a small subset of formats they support.

In both cases, these out of the box are limited to Tiff variants, even though they may support many different formats.

The list of supported formats could be statically expanded to a known set, but different runtime environments may have wildly different supported formats.

Therefore I propose a system where we ask the plugin implementations themselves to list what they support at runtime.

## Details

I propose the following changes:

1. Add a `dynamicExtensions: true` field to the `plugInfo.json` for HIO plugins.
2. Add a `GetSupportedFormatExtensions(std::vector<std::string>& formats)` method to HioImage or somewhere in the plugin system.
3. At runtime, when HIO is initialized for the first image it encounters, it asks any plugins with dynamicExtensions for their supported extensions. These are then statically associated with the plugin for the remained of the process lifetime.
4. Future invocations of HIO in the same process will not check again and will instead use the same associated extension list.

I believe this will be a relatively low cost at runtime.

## Concerns

My largest concern would be the thread safety of this, but I think USD already has several singleton patterns that can be used to handle this. 

## Benefits

The benefit of this would be that users don't need to modify their plugInfo.json to get support for new formats and there's a much lower risk of mismatch with their runtime. 

It would also mean that USD itself doesn't have to keep updating the format list over time, and can leave it to the image parser libraries themselves.
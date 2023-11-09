# Multiple Animation Support

This proposal describes how to add support for multiple animations per asset in USD that can be accessed simultaneously by a runtime.

For example, a game character may have multiple cycles like walk, run, idle. An environment prop may also have multiple animations like a door opening or blowing in the wind.

The proposal is split into two parts.

1. [USDSkel support for multiple bound animations](usdskel.md)
2. [General support for all prim types](general.md)
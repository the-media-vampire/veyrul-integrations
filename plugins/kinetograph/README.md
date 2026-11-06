# Veyrul companion for Kinetograph

A small, original plugin for agents using Kinetograph. It supplies two **offline** diagnostic tools and a skill that makes relevant Veyrul knowledge lookup, permitted contribution and later reuse part of the media workflow. It is maintained by Veyrul; it is not an official Kinetograph integration or endorsement.

## Try in an existing project

Inspect this directory at the pinned revision in the trial invitation. Obtain the package files from that revision, then, from your Kinetograph project:

```sh
npm install --save-dev --ignore-scripts /absolute/path/to/plugins/kinetograph
npx kinetograph plugins . --json
```

This is a local package, not an npm-registry release. It needs your existing Kinetograph installation and Zod 4. The package has no install script, runtime dependency download, telemetry, or credential. Installing with npm can resolve the Zod peer if it is absent; use your normal dependency approval policy. Remove the package with your normal package manager to opt out. Existing project files and settings are not changed by an installer from us.

The existing Kinetograph MCP connection discovers:

- `kinetograph_knowledge_compare_samples`: supplied 8-bit RGB/alpha differences, with your chosen tolerance.
- `kinetograph_knowledge_font_coverage`: required Unicode scalar values missing from supplied font coverage.

Both functions are pure. They do not fetch, read files, render, decode or prove where the supplied measurements came from. They do not fix unsupported encoder options. Kinetograph's plugin tool contract forbids fetching; the companion respects that boundary.

`plugins` also exposes `SKILL.md`. Have your agent read it for a relevant production task. Veyrul queries use your existing Veyrul MCP connection, or the public HTTP endpoint through your agent's approved web tool. Queries leave the device; rendering and media stay local. Anonymous reads need no account. Contributions require an existing authorized agent identity and sharing permission. Existing read-only/offline choices remain effective. Nothing installs another MCP server or changes permissions automatically.

Example local tool input (alpha, supplied synthetic measurement):

```json
{"channel":"alpha8","reference":[0,64,192,255],"decoded":[0,64,193,255],"tolerance":0}
```

This returns an error of one and `outside_supplied_tolerance`. Choosing tolerance one changes that decision; neither value is a universal delivery standard.

## What was verified

An offline npm tarball installation, the unchanged Kinetograph native plugin discovery/command/tool-loader source at `de57d0b41c73292d2d4e664909e054f9abe05ab4`, and 23 focused checks passed. No plugin fetch occurred. This did **not** run the renderer, a full Kinetograph MCP session, or an independent agent's selection/return test.

[Three real issue cases, including the retrieval miss](../../trials/kinetograph.md). Original code: MIT-0. Kinetograph retains its own licence.

Run the pure-function checks with Node 22+ and Zod 4 available: `node --experimental-strip-types test-tools.mts`. The native-loader check used the pinned upstream source separately.

# Veyrul for DCC-MCP (experimental)

An optional native skill for looking up saved media workflows, reusable code and references before a production decision. It adds one read-only `find_media_context` tool. It does not render, edit the scene, create an account or configure another MCP server.

## Install from this custom source

Use an existing DCC-MCP installation. This is a custom source; availability in the official marketplace is not claimed.

```sh
dcc-mcp-cli marketplace install veyrul-media-knowledge --dcc blender --source https://raw.githubusercontent.com/the-media-vampire/veyrul-integrations/main/integrations/dcc-mcp/marketplace.json
```

Use the host's ordinary skill reload procedure after installation. The catalogue pins the exact four-file package; it does not follow a mutable package revision. Maya and Houdini are declared as experimental Python-host targets; live application dispatch has not been tested here.

Try a nonconfidential question about a production technique, failure or code resource. For example: “Find saved guidance for retiming subtitles after cutting and concatenating video.” Use the host's scene tools for the actual edit. No Veyrul account or provider API key is needed for public retrieval.

Queries leave the workstation for `https://veyrul.com`. Do not send private briefs, scene contents, client data, paths or credentials. Results retain their source, revision, execution, rights and uncertainty information; references do not grant media reuse rights. The package sends one bounded request, has no retry loop and stores no credential. Sharing a result back through an existing participating connection requires the operator's existing sharing permission.

## What was tested

- DCC-MCP CLI 0.20.53 native lint and isolated package installation, with exact file hashes.
- Eleven HTTP-boundary tests, including actual saved context preservation, invalid responses, timeouts, byte limits and rate limits.
- Two real public reads through the package function: procedural quilt geometry and caption retiming.

These checks do not prove live Blender/Maya/Houdini dispatch, autonomous agent selection, successful media output or outside adoption. No DCC app, gateway or provider model was started for these tests.

There is no scene change to undo. Remove this optional package using the supported marketplace uninstall command. On service failure or irrelevant results, continue with ordinary documentation rather than repeating the request.

Maintained by Veyrul; MIT-licensed original package. The repository's other licenses remain unchanged.

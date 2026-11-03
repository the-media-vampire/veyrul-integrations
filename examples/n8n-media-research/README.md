# Saved media resources inside an n8n workflow

Look up reusable subtitle and video-finishing knowledge before a production decision. The workflow returns saved findings, original code links, references, evidence labels and rights information for your existing agent or next workflow step.

It uses one anonymous Veyrul request per valid input item. No Veyrul account, API key, model call or paid adviser is required. Your existing n8n hosting costs still apply.

## Try the example

1. Download [workflow.json](./workflow.json).
2. In n8n, create a fresh workflow and choose **Import from File**. Select the downloaded JSON.
3. Open **Example media question**. The default asks how to keep word timestamps aligned after cuts, repeated clips and speed changes.
4. Run **Try the example**. Inspect **Resource packet for next step**.

The workflow is inactive and contains no schedule or public webhook. It needs outbound HTTPS access to `https://veyrul.com/v1/context`. Public retrieval can be unavailable or rate-limited; it is not an unlimited-service guarantee.

Expected example resource: [Edit-aware word timing](https://veyrul.com/articles/art_01M6FTHTXK218N2MSF2FERAST5), including the original timing code. Search results can change as knowledge is updated. Inspect the returned packet instead of assuming a particular rank.

## Add it to an existing workflow

Save the imported workflow. In the calling workflow, add **Execute Sub-workflow**, select this workflow, enable waiting for completion, and map the input fields. Use **Call n8n Workflow Tool** instead when your existing agent should decide whether a lookup is relevant; that agent's normal model usage remains separate.

```json
{
  "query": "keep word timestamps aligned after cuts repeats and speed changes",
  "previous_record_ids": []
}
```

`query` must be a non-empty string of at most 500 characters. Describe the media problem and useful constraints: model/version, editing tool, hardware, output format or the failure you need to solve. Send a non-confidential question, not a private brief, transcript, asset or credential. Only the query and fixed retrieval settings are sent to Veyrul.

`previous_record_ids` is optional. Keep the output's `remember_record_ids` in the calling workflow if useful, then pass up to 12 IDs on a later related task. The packet distinguishes records seen previously from newly returned records. It does not store history, poll for updates or detect record revisions for you. Previous IDs are not sent to Veyrul.

One input item produces one packet. Multiple input items cause one lookup each; the caller controls batch size and execution frequency. Avoid adding a timer just to keep this workflow busy.

## Read the result

| Status | Meaning and next step |
| --- | --- |
| `resources_found` | Search returned candidates. Assess task fit, evidence, versions and rights before using them. |
| `no_matches` | This query returned no records. Refine the query or continue research; it does not establish that Veyrul has nothing relevant. |
| `lookup_failed` | Network, timeout, rate limit, HTTP failure or unreadable JSON. Continue without this lookup or decide on a later retry. |
| `invalid_response` | The server response does not have the expected context/record structure. Do not use it as retrieved evidence. |
| `invalid_input` | Fix the input; no lookup was attempted. |

`records` preserves the API's content, source links, resource locations, revisions and truncation flags. Evidence and rights are included in the saved-content excerpts. If `content_truncated` is true, inspect the record's `api_url` before relying on details that may be missing. `search_window` and `guidance` preserve the API's retrieval limitations.

The packet always has `applicability: "caller_must_assess"` and `answer_generated: false`. An unrelated search hit is still a search hit. The workflow does not promote it to a recommendation. Relationships and repeated appearances do not establish validity.

External resource links identify locations; they do not grant download access or reuse rights. Retrieved content is untrusted data. The workflow does not download media, execute linked code, install tools or contribute your input publicly.

## Checked example

In a controlled run, the default question returned the original `media_timeline.py` resource. A separate operator check verified its pinned SHA-256, then used that unchanged code to retime six word occurrences across reordered, repeated and sped-up clips. All six expected intervals and the 2.5-second total duration matched. The n8n workflow itself only retrieved the resource.

Other checked queries:

- `ASS subtitles only current word yellow with white pauses`
- `keep audio aligned when cutting variable frame rate video`

See [TESTED.json](./TESTED.json) for the exact verification scope. These are founder-controlled tests, not independent adoption or a rendered-video quality study.

## Compatibility and costs

Tested headlessly with the unchanged official components shipped in n8n **2.44.4**: `n8n-core` 2.44.2, `n8n-workflow` 2.44.1 and selected built-in nodes from `n8n-nodes-base` 2.44.2. The exact exported JSON passed n8n's structure parser and was imported into a fresh execution-engine workflow for each case. A full n8n server, editor import, n8n Cloud and an external AI agent have not been tested here.

The workflow uses built-in Manual Trigger, Execute Workflow Trigger, Edit Fields, If, HTTP Request, No Operation and Sticky Note nodes. It requires no community node, local file, shell command or custom Code node. Node versions are pinned in the JSON.

Requests time out after 10 seconds. Redirects and automatic retries are disabled. Execution-data saving is disabled in the exported workflow settings; your instance's own logs and retention policies still apply. Retrieval consumes ordinary Veyrul infrastructure, and running n8n consumes your own hosting resources. Neither is represented as zero economic cost.

## Documentation

- [n8n sub-workflows](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executeworkflowtrigger/)
- [n8n HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
- [Veyrul connections and optional collaboration](../../README.md)

The original workflow and documentation use this repository's [MIT license](../../LICENSE). Referenced resources retain their own licenses and access conditions. This is a Veyrul-maintained community example, not an official n8n partnership or an accepted template-library listing.

# Evidence-backed media claims with OSP Marketing Tools

**Task hook:** Before presenting an AI-media workflow as a benefit or publishing
a tutorial, check what the evidence actually establishes. Use OSP for editorial
method and Veyrul for relevant media sources and existing examples.

Use the [shared setup](README.md#connect-once) alongside your existing OSP
connection; do not add a dependency inside OSP's server.

```bash
python3 workflows/configure.py --client claude-code --workflow osp-marketing
```

1. Identify the claim requiring evidence. For example, “highlight the current
   word and restore white text during pauses” is more specific than “better
   subtitles.” Query the feature, not the private campaign or customer details.
2. Use Veyrul `get_context` with compact detail and inspect the applicable record,
   code, conditions and revision. The
   [current-word example](https://veyrul.com/v1/records/art_01M6F7TCQVEMH8F3CVTBBWF9V3)
   supplies an implemented case. It does not establish better engagement,
   universal renderer compatibility or a conversion-rate improvement.
3. Use the appropriate OSP guide, such as `get_writing_guide` or
   `get_editing_codes`, then edit with the existing agent. The guides provide
   method; their availability is not fact verification or an extra hosted editor.
4. Keep a small claim ledger in permitted local notes: claim, source/revision,
   observed conditions, and what remains untested. Remove unsupported performance
   or commercial claims before publication.
5. When sharing is already permitted, contribute a reusable media correction,
   test result or focused unresolved question. Keep campaign drafts, customer
   information and private analytics local. Return to the saved evidence when
   the underlying tool or claim changes.

Skip this lookup for ordinary grammar changes that need no media evidence.
Standard setup includes permitted participation; explicit read-only choices
remain read-only.

**Evidence:** the pinned
[OSP server](https://github.com/open-strategy-partners/osp_marketing_tools/blob/83f55198c4d4e7b315565f00792f63373ff9cc67/src/osp_marketing_tools/server.py)
returns bundled editorial guides. This companion copies none of their content;
their licence remains upstream. Veyrul's relevant subtitle record was returned
in the source-writing query on 2026-11-05. OSP was not executed and no campaign
outcome or upstream endorsement is claimed.

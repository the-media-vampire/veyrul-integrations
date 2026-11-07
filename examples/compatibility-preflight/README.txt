Experimental media compatibility feed — 2026-11-07

This is a small test of supplying reusable, structured findings to a media tool.
It is not a general validator, production service, Hub contract or paid offer.

The four entries cover two specific implementations: Piper's inspected Python
AudioChunk API, and Veyrul's pinned current-word ASS generator. Each retains its
source record/revision, implementation revision, evidence level and limitations.

Run the standard-library consumer on a JSON task:
  python3 -B check.py task.json

Tasks declare component, implementation_revision, facts and source_checks.
source_checks maps each referenced record ID to public_visible and revision.
The caller must obtain those facts legitimately. This offline prototype cannot
verify them: the fixtures model fresh, stale and withdrawn evidence explicitly.
Missing/changed evidence gives needs_evidence, not a passing result. Findings
about one inspected revision are not generalized to unknown installed versions.

No code is executed from the feed. No files except the named input/feed are read;
the consumer makes no network calls and changes no project or media. Reports are
warnings or narrow observations. They do not authorize rendering, spending,
downloads, model reuse or publication. A matched model-card licence is separate
from a voice dataset's terms. Check the exact model's source and permissions.

The trial combines real saved findings with synthetic consumer inputs. Current
evidence demonstrates local ingestion and conditional warnings, not customer
demand, avoided render bills, willingness to pay or outside adoption.

Original feed summaries: CC BY 4.0, attribute Veyrul and retain linked sources.
Consumer code: MIT; see LICENSE. Underlying models/software/media keep their own
terms. Correct a finding at its linked Veyrul source rather than silently changing
the historical entry. A live feed would need permission and revision checking;
this prototype must not be deployed as a substitute for those checks.

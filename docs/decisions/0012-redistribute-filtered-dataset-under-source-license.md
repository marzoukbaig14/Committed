---
id: 0012
title: Redistribute filtered CommitChronicle derivative under source license terms
date: 2026-05-30
status: accepted
supersedes: []
superseded_by: []
relates_to: []
tags: [data, infra]
---

## Context
We plan to publish a filtered subset of CommitChronicle to the Hugging Face Hub
as `committed-train`. CommitChronicle aggregates commits from public GitHub
repositories that carry permissive licenses (MIT, Apache-2.0, BSD-3-Clause) and
is tagged "other" on the Hub. Its terms require that any reuse abide by the
original repository licenses, including attribution, and it provides per-row
provenance (the `repo` and `license` fields) so attribution is possible. It also
warns that the data may contain sensitive information (emails, API/SSH keys) that
was committed to public repositories. Whether and how we may redistribute a
filtered derivative was an open question (see MASTER, Licensing).

## Decision
Publish the filtered derivative under the source's terms:
1. Retain the `repo` and `license` columns in `committed-train`; the data filter
   must not drop them, so per-row provenance is preserved.
2. In the dataset card, attribute CommitChronicle: link the source dataset and
   cite its paper (arXiv 2308.07655), and state the upstream license situation.
3. Carry the sensitive-data caveat forward in the dataset card.
Automated scrubbing of sensitive data is deferred; for v1 it is documented as a
known limitation rather than implemented.

## Consequences
We can publish `committed-train` publicly with a clear, defensible licensing
basis, and the dataset card demonstrates proper provenance handling. The data
filter is now constrained to preserve the `repo` and `license` fields in its
output schema. We take on a small ongoing documentation burden on the card. The
sensitive-data risk remains and is noted as a known limitation to revisit if a
scrubbing pass is added later. Unlike the diff token cap (a tunable
hyperparameter, not logged), this is a standing constraint the project carries.
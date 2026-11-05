# Community Evidence Packs (schema 2, v0.6.0)

A community pack models the vocabulary and discourse conventions of a **context of practice**. Examples: software teams, an office, academic research, a gaming community. It never models a person's identity. VozNativa never infers a community from a text or an author. A pack applies only when the request names it (`--community tech`).

Data: `voznativa/data/community_packs/<id>.yml`. Validator and behaviour: `voznativa/community.py`. The package refuses to load a pack that breaks a rule below.

## Taxonomy

Every item has one category, and the category decides how it is treated:

| category | what it is | example | default behaviour |
|---|---|---|---|
| `terminology` | the field's name for a thing; translating it loses precision | deploy, pull request, sprint | `preserve` |
| `jargon` | insider shorthand, legitimate among peers, opaque outside | stack, call, nerf | `avoid_outside` or `preserve` |
| `borrowing` | a foreign word with a common Portuguese equivalent | feature, deadline | `avoid_outside` |
| `slang` | informal and temporal (see `references/slang/schema.yml`) | tankar | `avoid_outside` |
| `meme` | a formula tied to a moment | — | `avoid_outside` |
| `discourse_habit` | a recurring way of saying things | alinhar, subir para produção | `avoid_outside` |

Behaviours:
- **`preserve`**: kept where the author wrote it. With the community requested, editorial `anglicism_out_of_domain` findings on it are withdrawn, and the withdrawn findings are listed in the report.
- **`avoid_outside`**: kept where the author wrote it, never added outside `legitimate_in`.
- **`never_add`**: kept, never added.

A slang or meme item marked `preserve` must say it is temporal.

## Admission rule

An item enters a pack only with:
- its context of practice;
- its category and behaviour;
- the channels where it is legitimate;
- a known false-positive case;
- an evidence level.

A pack moves out of `draft` only with evidence E2 or higher and listed sources. Generation (adding a term) needs a non-draft pack at E2 or higher. **No shipped pack meets that; all four are `draft`, E0.**

## Precedence

```text
invariants > explicit instruction > author voice > genre/channel/audience
  > regional / temporal / community evidence > generic editorial rules
```

The author's own words win over a pack. A pack's terms win over a generic editorial rule only by withdrawing that rule's anglicism finding on a preserved term. A pack never forces a term into a text.

## Review signals

When a candidate adds a pack term the source did not have, the engine review flags it as `community_term_introduced`:
- `info` for terminology;
- `major` for jargon, borrowings, slang and discourse habits.

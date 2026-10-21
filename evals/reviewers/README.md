# Reviewer registry

Empty on purpose: no external reviewer has registered yet.

`voznativa review` and `voznativa blind-review` sign with a local HMAC key by
default. That key is a shared secret of the machine's OS user: the developer,
or an agent running as that user, can sign with it too, so an HMAC review is
never counted as independent (`independence: not_established`).

A reviewer who is not the developer signs with their **own** SSH key, which never
leaves their machine:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/voznativa_review -C "nome@exemplo.org"
# send ~/.ssh/voznativa_review.pub to the maintainer, then:
voznativa blind-review tarefas.json --reviewer "Nome" --ssh-key ~/.ssh/voznativa_review \
  --principal nome@exemplo.org --out respostas.jsonl
```

The maintainer adds one line to `allowed_signers` (`nome@exemplo.org ssh-ed25519 AAAA...`)
and one entry to `registry.json`:

```json
"nome@exemplo.org": {"declared_name": "Nome", "relationship": "independent",
                      "added": "2026-10-21", "statement": "did not write or read the engine"}
```

What each property means in `voznativa.review.assess`:

| Property | Shown by | Not shown |
|---|---|---|
| integrity | signature verifies over the exact JSON | — |
| key possession | SSH: the private key of a registered principal; HMAC: anyone with this machine's key file | that a person, not a process, used the key |
| declared identity | `judge_id`, principal, OS user, registry name | who the person is |
| independence | at most `declared` in this registry | that the declaration is true |

The registry is written by the maintainer, so "declared independent" is a recorded
statement, not proof. Reports must say so.

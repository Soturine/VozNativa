"""Universal Linguistic Corpus Platform (v0.6.0).

Small contracts with one owner each:

* ``registry``   — what a source is and what has been proven about it
* ``policy``     — what an operation on it is allowed to do
* ``connectors`` — bounded, read-only access to local or remote data
* ``processing`` — provenance, normalisation, deduplication, stable splits

Nothing here is needed to rewrite a text: the engine runs without corpora,
and only versioned, authorised derived artefacts reach the other layers.
"""

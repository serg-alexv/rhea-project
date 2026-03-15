# Next Steps

1. Build entity-link manifest joining page/project IDs between `ios/play-extraction` JSON and Firebase thumbnail filenames.
2. Tag JSON keys into stable ingest schema classes (identity, ownership, timestamps, media, routing).
3. Produce Mongo-oriented document templates from extracted keys (without writing to DB yet).
4. Produce Qdrant-ready doc chunks from protocol/docs corpus with source path provenance.
5. Separate cache/debris from source corpora using deterministic path allow/deny rules before bulk indexing.

# Decisions

This section outlines a log of architectural decisions for record keeping.

## Decision Log

### ADR-001: Structure the trading chain as a pipeline

**Date:** 2026-04-16
**Status:** Accepted

#### Context
The original idea was th set up a server that would periodically launch a background job. This server would also offer extra endpoints. After revising the frequency at which this pipeline would be expected to run, a server felt unnecessary.

#### Decision
Run the pipeline locally on a schedule. If a need eventually emerges to run it remotely, we would go with [Modal](https://modal.com/) to do that.

#### Consequences
- The scheduler is Mac-native in the first iteration
- The job may not run due to the machine being offline

#### Alternatives Considered
FastAPI server

### ADR-002: Use Google Sheets as the database

**Date:** 2026-04-16
**Status:** Accepted

#### Context
We need to store trade metadata, such as the trading thesis, expiry dates, and so on, to do that, we need a storage layer

#### Decision
Google sheets allows us to read and write structured data without the overhead of a fully blown DB

#### Consequences
- We can view and interact with the database
- There is a risk that human modifications may corrupt trade

#### Alternatives Considered
PostgreSQL vs Supabase was considered here, but it was more complex


### ADR-003: Use SQLite for the cache storage

**Date:** 2026-04-16
**Status:** Accepted

#### Context
We want to be able to cache some data where flat file modelling may get complicated, so we need an alternative storage layer

#### Decision
Local SQLite it is

#### Consequences
- We can run a proper database locally
- If the file gets lost or corrupted, our entire database dies
- Migrating to another DB variant may come with costs

#### Alternatives Considered
Keeping the data in the same layer as Google Sheets, but it may get messy


### ADR-003: Use ChromaDB for learnings

**Date:** 2026-04-16
**Status:** Accepted

#### Context
We are likely to be generating a lot of learnings during this process and semantic search layer is likely to become important

#### Decision
ChromaDB offers a local, zero-infra, Python-native solution, we will go with that.

#### Consequences
- Our entire database is stored on a local machine

#### Alternatives Considered
Local markdowns were considered as extra context and these may work well for ~50 or so learnings, but beyond that point Chroma becomes rather useful. We are working with the assumption that we will hit that point quickly.
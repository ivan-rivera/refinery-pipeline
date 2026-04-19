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
Google sheets allows us to read and write structured data without the overhead of a fully blown DB. Moving forward, we may choose to introduce ChromaDB for vector storage and SQLite for more complex DB modelling, but for now Google Sheets will be our data storage layer, to keep things simple.

#### Consequences
- We can view and interact with the database
- There is a risk that human modifications may corrupt trade

#### Alternatives Considered
PostgreSQL vs Supabase was considered here, but it was more complex

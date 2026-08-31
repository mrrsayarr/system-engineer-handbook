# Idempotent Message Consumer

This example models the correctness boundary for an at-least-once consumer:
deduplication and the business side effect commit in one SQLite transaction.
The message broker acknowledgement happens only after the transaction commits.

```bash
python consumer.py
```

The `processed_messages(message_id)` primary key makes concurrent/replayed
delivery safe. A production consumer also needs an inbox retention policy,
poison-message quarantine, bounded retries, schema validation, and an outbox if
it publishes a subsequent event. SQLite here demonstrates atomicity; it is not a
claim that SQLite is the right production ledger.

Failure drills: run the same message twice, inject an exception before commit,
and inject an exception after a simulated broker delivery but before the ack.
The business total must be applied once and the message must be retriable.

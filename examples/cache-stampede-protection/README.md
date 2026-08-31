# Cache Stampede Protection

`singleflight_cache.py` implements a bounded, in-process demonstration of
stale-while-revalidate. One caller refreshes a key; concurrent callers receive
fresh data or acceptable stale data rather than multiplying origin load.

```bash
python singleflight_cache.py
```

The example uses a lock only to coordinate local callers. A multi-instance
deployment needs a distributed lease or ownership mechanism with fencing, and
the origin still needs a concurrency budget. TTL jitter, negative caching,
version checks, and bounded stale age are production requirements.

Failure drills:

1. Make `origin()` sleep longer than the refresh timeout; verify callers do not
   create an unbounded origin queue.
2. Raise from `origin()`; verify stale data is served only inside `stale_for`.
3. Run multiple processes; observe that the local lock does not coordinate them.

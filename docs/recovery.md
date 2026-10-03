# Recovery record

The earlier project existed in a temporary execution workspace and was committed
as `679b4f8`. The user-facing links pointed to local workspace paths, without a
durable attachment. By the time download failure was investigated, that workspace
had reset and no original repository, archive, Git bundle or report attachment
was accessible.

This starter package restores the implementation from retained conversation
records, retrieves the pinned benchmark from its primary archive, creates a new
dependency lock, and runs fresh checks. It is not a byte-for-byte copy of the
original commit. The original raw pilot logs, lock, report attachment and Git
history are unavailable. They have not been invented or represented as recovered.

Historical results in README and the campaign notes are summaries recorded in
the conversation. Fresh checker output and test results refer to this rebuild.
New research should log its own code revision, seeds and complete artifacts.

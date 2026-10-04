```text
Document:    Current Public Repository Target Confirmation for C(16,5,3)
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      27c2978e7af7833a14c30601b6d1bdbc69504d81c2316bea85d194cef2f335e9
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Current public repository target confirmed

The maintained Covering Repository publicly lists **65 blocks for `C(16,5,3)`**, as retrieved on 2026-10-04. This is an upper listing, not a claim that the exact covering number is 65. The current lower bound was not supplied by this archive and was not verified here.

The public [Download page](https://coveringrepository.com/download.aspx) explicitly links to [Download whole (v,k,t) archive in .txt format](https://coveringrepository.com/download_archive_vkt.aspx). That advertised unauthenticated archive returned HTTP 200 at 2026-10-04T21:17:36.981055Z: 171,741 bytes of plain text, with 9,490 unique parameter rows. SHA256: `f9071fd1b35e2b0ff2f8a4e83a4ecf60c28d25823f4e1f031cd5cd2c26b882a5`.

Line 395 is exactly `16\t05\t03\t03\t\t65` (tabs escaped here). Its fields are `(v,k,t,m,blocks)=(16,5,3,3,65)`; ordinary coverings have `t=m`, so this is the requested target. The archive has no target author, target date, history, lower bound, or block witness.

As a freshness crosscheck, all 100 numeric rows from the previously fetched [latest ordinary improvements page](https://coveringrepository.com/systems.aspx?li=2) exactly match the archive. Those rows span 2026-09-26 through 2026-10-04, including the October 4 listings `(42,17,6,6):1440`, `(63,19,5,5):1965`, and `(59,25,5,5):242`. This shows the archive includes the sampled post-March improvements; it is not merely the frozen March Gordon export. It does not establish the archive's exact generation time or prove all possible improvements are present.

This supplement resolves the outstanding current-upper-listing question in the earlier [source refresh](../post-march-public-source-refresh/README.md). That frozen note remains unchanged. The earlier direct target detail URL returned 403 and was not retried; no authentication, payment, access-control bypass, researcher contact, or external publication occurred. The public archive link was discovered from the site's own accessible Download page.

`source-checks.json` saves exact URLs, retrieval times, hashes, the target line, and all 100 comparison rows. Raw network responses remain in ignored scratch storage. No new covering witness was claimed or downloaded, and no solver ran. No additional algorithm papers were screened after the public target listing was resolved.

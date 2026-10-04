```text
Document:    Fresh Primary Source Check for C(16,5,3)
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      1c597d55c0ccbcab857c20e69267ee0799d2b630266876c3a270bcab1b558f01
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Freshly retrieved primary record

The currently linked primary La Jolla database records **61 ≤ C(16,5,3) ≤ 65**.
Its best recorded construction has 65 blocks, attributed to **Rade Belic** with
timestamp **1997-08-06 00:00:00**. The only earlier improvement in this entry is
68 blocks, attributed to "JCD article" on 1996-11-14. No 64-block improvement or
witness is listed in this primary metadata entry.

This is a fresh retrieval of a **frozen database**. The repository README says
the La Jolla database was frozen in March 2026. Its current version is 1.2,
published 2026-04-24. These records do not establish that no later improvement
exists elsewhere.

## Current source route and evidence

The old `ljcr.dmgordon.org` host did not resolve during the refresh. Dan Gordon's
current [covering-designs page](https://dmgordon.org/covering-designs/) links the
concept DOI [10.5281/zenodo.10779736](https://doi.org/10.5281/zenodo.10779736).
Its API resolves to [record 19735294](https://zenodo.org/records/19735294).

| Source | Retrieval time, UTC | Response SHA256 |
| --- | --- | --- |
| Current primary webpage | 2026-10-04 04:18:08.549273 | `a5cc2312afc8dedd17c52410c34d518396d0a42982b2af429c8dc54f9e7170e3` |
| Zenodo primary metadata | 2026-10-04 04:18:57.850349 | `5c79d859957bcd3d4b91dcdcf9f2c3ccb097a6eacd94e24dd5520cdda83394df` |
| coverdata.json | 2026-10-04 04:19:33.351223 | `9e7da3710921066b10234fdc95379a18df3a7d3ae0f8a08ae188ea6bbca92f87` |
| Repository README | 2026-10-04 04:19:33.351336 | `8e9d653878c36663c6b6ce60b321a86ef4514def41f983ad3123d4e47e5afb1d` |

The exact metadata URL is
[coverdata.json](https://zenodo.org/api/records/19735294/files/coverdata.json/content).
The extracted key is `C(16,5,3)`. All downloaded metadata/access-documentation
files match both their published byte lengths and the MD5 checksums in Zenodo's
record. SHA256 hashes separately preserve the exact retrieved response bytes.

The current primary webpage explicitly points to
[coveringrepository.com](https://coveringrepository.com) for more recent
improvements. A fresh request to the
[current parameter entry](https://coveringrepository.com/systems.aspx?v=16&k=5&t=3&m=3)
returned HTTP 403 with a browser challenge at 2026-10-04 04:17:03.560370 UTC.
That response hash is
`a4025e459a60dbb9a2001899995f08bc63e48abf27fffd83e401e8ed6c822a58`.
The in-app and Chrome browser tools each reported that the browser was
unavailable. No challenge was bypassed. Therefore the site's latest entry and
any later linked record were **not freshly verified** in this refresh; the
earlier saved 65-block record must not be presented as a new live check.

Only the 8.32 MB metadata file and small documentation/code files were fetched.
The 4.19 GB `covers.json` witness archive was not downloaded. No source code
downloaded from the repository was executed, and no researcher was contacted.

`sources.json` records all requested/final URLs, UTC times, status/error values,
byte lengths and hashes. A DNS failure has no HTTP response; its zero-byte file
is only a placeholder for that failed request. Raw response bodies are outside
Git in `experiments/scratch/public-bound-refresh-20261003/`.

`check.py` reads back all saved response hashes and the exact primary entry.
It rejects four damaged-source/result controls. This validates the saved
evidence, not the mathematical lower-bound proof or a new covering witness.

# Recovered LJCR benchmark provenance

This starter package was reconstructed on 2 October 2026 after the original
execution filesystem became unavailable. The source bytes below were fetched
again from the immutable Zenodo record, and checks were run anew. This package
does not recreate missing historical experiment logs or the full supplied
research report.

The benchmark `../baselines/belic-1997.txt` is the exact `C(16,5,3)` entry
from the **La Jolla Coverings Repository**, version **1.2**, published on
**24 April 2026** by **Daniel Gordon**:
[DOI 10.5281/zenodo.19735294](https://doi.org/10.5281/zenodo.19735294).
The dataset uses [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The archival improvement record attributes the 65-block construction to
**Rade Belic**, dated **6 August 1997**. Point labels and block order are
preserved; the witness has one space-separated block per line and a final newline.

`zenodo-record-19735294.json` preserves the newly retrieved published dataset
metadata. `ljcr-c16-5-3.json` records retrieval, checksums, the relevant metadata
entry, and an independent exhaustive verification. `zenodo-c16-5-3.fragment.txt`
preserves the exact 1,070-byte source entry, including its trailing comma.
`ljcr-LICENSE.txt` preserves the archived license notice.

| Artifact | Size / range | Check |
| --- | --- | --- |
| Complete `coverdata.json` | 8,319,503 bytes | Published MD5 `b2c626b07f216aac830d344eff5ad523` verified |
| `covers.json` entry | Inclusive bytes 18,860,330–18,861,399 | HTTP 206 and exact `Content-Range` checked; fragment SHA-256 `582ee63e54ba947af3155e03e6055027a92c55c1fda9b78ec021b5b693968d3c` |
| Plain-text witness | 65 blocks | SHA-256 `89e4f68acba5d2cbee73e22d07dd1030e540b920fc7541619a065e998dc7d43f`, matching the report hash retained in the conversation |
| Complete `covers.json` | 4,191,522,340 bytes | Published MD5 `bb59d977afd6724b32dcc187f68a229c` **not verified** |
| Archived license | 621 bytes | Published MD5 `f0922cdd282cdddc058d5d8c77eda8e7` verified |

The complete metadata records `size: 65`, `low_bd: 61`, and Belic's
attribution/date. Independent enumeration confirms 65 distinct 5-subsets on
points 1–16, all 560 triples covered, and 650 triple incidences. The triple
multiplicities are 497 once, 56 twice, two three times, and five seven times.
These checks establish the archived construction and metadata, not current
worldwide novelty or the exact minimum covering number. Fragment and witness
SHA-256 values are locally computed reproducibility checks, rather than
publisher-issued excerpt checksums.

From the repository root, use Python 3.11 or later:

```sh
python scripts/fetch_ljcr.py
```

The script checks the complete metadata MD5, requests only the exact archive
entry, checks the byte range and hashes, verifies coverage, and rewrites the
small benchmark and provenance files. Downloads use the inherited proxy and
CA trust with TLS verification enabled. Raw downloads stay outside the repository
in `covering64-ljcr` under the system temporary directory. The recovery run used
`--cache-dir /workspace/scratch/ljcr --download-timeout 120`.

An optional complete archival audit can be run separately:

```sh
python scripts/fetch_ljcr.py --full-archive --download-timeout 7200
```

That mode downloads the entire payload sequentially, checks length and published
MD5, records SHA-256, and extracts the entry using a line-by-line scan. It never
loads the full 4.19 GB archive into memory. **It was not run for this recovery.**
Provenance records full archive verification only after that checksum passes.
No downloaded source code is executed by this workflow.

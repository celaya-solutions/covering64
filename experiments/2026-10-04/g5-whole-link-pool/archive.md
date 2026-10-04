```text
Document:    Fixed G5 Pool Result Archive
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9a5149034d8c15b2586f2c3c262d83f3f08384204f99cb46d371c158130f032b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exact result preservation

The 6,924,774-byte `result.json` is preserved locally and ignored by Git. `result.json.gz` contains its unchanged bytes and is kept in Git. Restore the original from the compressed file before replaying tools that bind its full-file SHA256. Raw models, values and duals remain in ignored scratch storage. The proof bundle has a separate archive manifest.

From this folder, restore the exact result with Python: `python3 -c "import gzip,pathlib; p=pathlib.Path('result.json.gz'); p.with_suffix('').write_bytes(gzip.decompress(p.read_bytes()))"`.

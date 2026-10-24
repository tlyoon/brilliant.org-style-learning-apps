# Controlled PDF and activity passage evidence

This is a bounded independent **text-location** check, not an academic correctness oracle.

Run (on an authorized workstation):

    python scripts/audit_source_passages.py --package PRIVATE_INSTALLED_PACKAGE.json --source-manifest content/source-manifests/chapter-9-section-9-4.json --pdf PRIVATE_CONTROLLED_SOURCE.pdf --anchors PRIVATE_QUOTATION_ANCHORS.json

The private optional anchors file is a JSON array of records such as:
    [{"activityId":"fixture-01","pageIndex":1,"quotedText":"A sufficiently long source sentence or paragraph describing a physical model and its constraints."}]

- The input PDF is checked byte-for-byte against its manifest SHA-256 **before** text extraction.
- The page number is a 1-based PDF page index; it is not the textbook's printed page number.
- Exact NFKC/whitespace-normalized passages longer than 40 characters and seven words must occur on exactly one page and match the reported PDF page.
- Missing, short, ambiguous and extraction-damaged quotations are REVIEW_REQUIRED. A provable page misattribution is a source-citation FAIL.
- Positive evidence means only VERIFIED_TEXT_ONLY; it does **not** prove the generated answer, interpretation, numerical reasoning or EN/MS/ZH translations. The release gate remains blocked until independent academic evidence passes.
- The tool emits only activity identifiers, page indexes, excerpt hashes and status; never raw controlled PDF excerpts. Do not commit the controlled textbook or private quotation files.
- For Section 9.4, the exact 985,648-byte controlled PDF was independently fetched read-only from Drive and SHA-256 matched the source manifest: 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578. Text extraction gave nine pages. The installed package has 18 activities but no page-specific quotation receipts, hence 0 VERIFIED_TEXT_ONLY, 18 REVIEW_REQUIRED and zero demonstrated citation defects.
- The smallest next step is to derive passage-level activity citations from the controlled source and verify each under this contract. Do not substitute broad sourceLocation fields or generative model self-attestation.

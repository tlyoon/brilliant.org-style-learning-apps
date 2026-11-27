# BSA283 PDF LaTeX audit and source-verification stall repair

The live Bosla owner on Yoga6 does not invoke PDF LaTeX, pdflatex, xelatex, lualatex or latexmk. Its real process reads text from the one selected original Serway Section 9.1 source.pdf with pdftotext. The Bosla JSON generation prompt forbids LaTeX commands; three outside PDFs are a retired historical trial, not a production prerequisite.

The real operational problem: repeated pdftotext on same PDF plus parent RUNNING heartbeat even with no original source child log progress for >35m. Source passages now use an in-process SHA256-keyed extracted-page cache. Original selected PDF is re-opened and SHA-checked on every request, again around real extraction. Changed or untrusted source fails closed; no second source or outside file.

Original owner CLI runs unbuffered and emits flushed step progress to private child logs. Parent progress watcher checks child log bytes independently from its own heartbeats; after 20min silent owner, kill only that process tree and classify as local implementation failure, preserving signed science receipts and allowing code repair. Full science/translation/diagram academic PASS is NOT inferred; 15 of 429 signed tasks remain and 90 full activity gates open.

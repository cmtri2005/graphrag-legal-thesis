"""What the crawl has on disk, and what it knows about it.

`documents` is the file layout (one JSON per document per stage). `manifest`
is the SQLite side-table that makes delta crawling possible: when each document
was last fetched, what the sitemap said then, and whether it is gone.
"""

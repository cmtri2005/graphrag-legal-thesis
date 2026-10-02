"""Building the document graph.

`expand` walks outward from seeds through genealogy edges only. `diagram` reads
the inbound relations that `references[]` never records — without it, forward
BFS cannot discover the documents that amended the corpus.
"""

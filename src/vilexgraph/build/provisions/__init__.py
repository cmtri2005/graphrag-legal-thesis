"""Structure inside a document: Chương / Điều / Khoản / Điểm.

`tree` fetches the skeleton the server already knows. `text` attaches the body
text to it — an exact join for modern records, which carry the tree node's own
uuid on each paragraph, and marker matching for older ones that do not.
"""

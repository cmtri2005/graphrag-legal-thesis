"""Everything that talks to vbpl.vn.

Two hosts, two clients, on purpose: `api_client` speaks to the JSON gateway
(`vbpl-bientap-gateway.moj.gov.vn`), and `sitemap` reads the XML shards on
`vbpl.vn` itself. A third lives in `provisions.tree`, which drives a Next.js
server action and needs its own retry policy — see its docstring for why the
three are not one.
"""

"""Inspect Galaxy's index."""

import pprint
from whoosh.index import open_dir
# from whoosh.query import Every
from whoosh.qparser import QueryParser

GALAXY_INDEX = '/home/cameron/dev/galaxy/galaxy/database/tool_search_index/default'
TEST_INDEX = 'index'

INDEX = GALAXY_INDEX
# INDEX = TEST_INDEX

ix = open_dir(INDEX)
print("Schema:")
pprint.pprint(ix.schema)
qp = QueryParser("name", schema=ix.schema)
with ix.searcher() as s:
    q = qp.parse(u"group")
    results = s.search(q)
    pprint.pprint(results[0])

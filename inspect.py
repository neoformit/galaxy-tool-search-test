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

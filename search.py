"""Whoosh search prototyping."""

import sys
import json
import re
import os
import shutil
from types import SimpleNamespace
from typing import (
    Dict,
    List,
    Union,
)

from whoosh import (
    analysis,
    index,
)
from whoosh.fields import (
    ID,
    KEYWORD,
    Schema,
    TEXT,
    NGRAMWORDS,
)
from whoosh.scoring import (
    BM25F,
    Frequency,
    MultiWeighting,
)
from whoosh.qparser import (
    MultifieldParser,
)
from whoosh.writing import AsyncWriter

# !!! our stuff
import pprint
from utils import to_unicode
# !!!

TOOLS_JSON = 'data/tools.json'
# TOOLS_JSON = 'data/machine.json'
INDEX_DIR = 'index'
# INDEX_DIR = '/home/cameron/dev/galaxy/galaxy/database/tool_search_index/default'

TOOL_NAME_BOOST = 20.0
TOOL_ID_BOOST = 20.0
TOOL_STUB_BOOST = 10.0
TOOL_DESCRIPTION_BOOST = 5.0
TOOL_SECTION_BOOST = 2.5
TOOL_HELP_BOOST = 1.0
TOOL_LABEL_BOOST = 2.0
TOOL_SEARCH_LIMIT = 5

TOOL_NGRAM_ENABLE = True
TOOL_NGRAM_FACTOR = 0.2
TOOL_NGRAM_MINSIZE = 3
TOOL_NGRAM_MAXSIZE = 4

CanConvertToFloat = Union[str, int, float]
CanConvertToInt = Union[str, int, float]


class ToolBoxSearch:

    def __init__(self):
        """Create searcher."""
        self.schema = Schema(
            id=ID(stored=True, unique=True),
            id_exact=TEXT(
                field_boost=TOOL_ID_BOOST * 10,
                analyzer=analysis.IDTokenizer() | analysis.LowercaseFilter(),
            ),
            name=TEXT(
                field_boost=TOOL_NAME_BOOST * 10,
                analyzer=analysis.IDTokenizer() | analysis.LowercaseFilter(),
            ),
            stub=KEYWORD(field_boost=TOOL_STUB_BOOST),
            description=TEXT(
                field_boost=TOOL_DESCRIPTION_BOOST,
                analyzer=analysis.StemmingAnalyzer()),
            section=TEXT(field_boost=TOOL_SECTION_BOOST),
            help=TEXT(
                field_boost=TOOL_HELP_BOOST,
                analyzer=analysis.StemmingAnalyzer()),
            labels=KEYWORD(field_boost=TOOL_LABEL_BOOST),
            name_ngrams=NGRAMWORDS(
                stored=True,
                minsize=TOOL_NGRAM_MINSIZE,
                maxsize=TOOL_NGRAM_MAXSIZE,
                field_boost=TOOL_NAME_BOOST * TOOL_NGRAM_FACTOR,
            ),
        )
        self.rex = analysis.RegexTokenizer()
        self.index = self._index_setup()

    def _index_setup(self) -> index.Index:
        """Create or return the whoosh index."""
        if not os.path.exists(INDEX_DIR):
            os.makedirs(INDEX_DIR)
        if index.exists_in(INDEX_DIR):
            idx = index.open_dir(INDEX_DIR)
            try:
                assert idx.schema == self.schema
                return idx
            except AssertionError:
                print(
                    f"Index at {INDEX_DIR} uses outdated schema,"
                    " creating new index")
        return index.create_in(INDEX_DIR, schema=self.schema)

    def build_index(self) -> None:
        """Prepare search index for tools loaded in toolbox."""
        if os.path.exists(INDEX_DIR):
            shutil.rmtree(INDEX_DIR)
        self.index = self._index_setup()
        tool_ids = _read_tool_list()
        with AsyncWriter(self.index) as writer:
            for tool in tool_ids:
                tool_data = self._create_doc(tool)
                writer.update_document(**tool_data)

    def _create_doc(self, tool) -> Dict[str, str]:
        add_doc_kwds = {
            "id": to_unicode(tool.id),
            "id_exact": to_unicode(tool.id),
            "description": to_unicode(tool.description),
            "section": to_unicode(tool.panel_section_name),
            "help": to_unicode(tool.help),
        }
        if tool.name.find("-") != -1:
            # Replace hyphens, since they are wildcards in Whoosh causing false positives
            add_doc_kwds["name"] = (" ").join(token.text for token in self.rex(to_unicode(tool.name)))
        else:
            add_doc_kwds["name"] = to_unicode(tool.name)
        if tool.guid:
            # Create a stub consisting of owner, repo, and tool from guid
            slash_indexes = [m.start() for m in re.finditer("/", tool.guid)]
            id_stub = tool.guid[(slash_indexes[1] + 1): slash_indexes[4]]
            add_doc_kwds["stub"] = (" ").join(token.text for token in self.rex(to_unicode(id_stub)))
        else:
            add_doc_kwds["stub"] = to_unicode(id)
        # if tool.labels:
        #     add_doc_kwds["labels"] = to_unicode(" ".join(tool.labels))
        raw_help = tool.help
        if raw_help:
            try:
                add_doc_kwds["help"] = to_unicode(raw_help)
            except Exception:
                # Don't fail to build index if help can't be converted
                pass

        add_doc_kwds["name_ngrams"] = add_doc_kwds["name"]

        return add_doc_kwds

    def search(self, q: str) -> List[str]:
        """Perform search on the in-memory index with weighting."""
        # Change field boosts for searcher
        self.searcher = self.index.searcher(
            weighting=MultiWeighting(
                Frequency(),
                help=BM25F(K1=0.5),
            )
        )

        fields = [
            "name",
            "id",
            "id_exact",
            "description",
            "section",
            "help",
            "labels",
            "stub",
            "name_ngrams",
        ]
        self.parser = MultifieldParser(fields, schema=self.schema)

        cleaned_query = q.lower()
        cleaned_query = " ".join(
            token.text for token in self.rex(cleaned_query))
        # Use asterisk Whoosh wildcard so e.g. 'bow' easily matches 'bowtie'
        parsed_query = self.parser.parse(cleaned_query)
        hits = self.searcher.search(
            parsed_query, limit=float(TOOL_SEARCH_LIMIT),
            sortedby="", terms=True)

        scores = [
            x[0] for x in hits.top_n
        ][:TOOL_SEARCH_LIMIT]

        with open(TOOLS_JSON) as f:
            tool_data = json.load(f)
        pprint.pprint([
            {
                'score': score,
                'details': get_tool_by_id(hit['id'], tool_data) or hit['id'],
                'matched_terms': hit.matched_terms(),
            }
            for hit, score in zip(hits[:TOOL_SEARCH_LIMIT], scores)
        ])
        return hits


def _read_tool_list():
    """Read tools list from JSON file."""
    with open(TOOLS_JSON) as f:
        tools = json.load(f)
    tool_list = []
    for tool in tools:
        tool_list.append(SimpleNamespace(**tool))
    return tool_list


def get_tool_by_id(tool_id, tool_data):
    """Return dict for given tool id."""
    for t in tool_data:
        if tool_id == t['id']:
            return t


def main():
    """Search for tools."""
    query = sys.argv[1]
    toolbox = ToolBoxSearch()
    if query == '--build':
        toolbox.build_index()
    else:
        results = toolbox.search(query)


if __name__ == '__main__':
    main()

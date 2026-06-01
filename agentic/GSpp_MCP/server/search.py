import re
from typing import List, Dict, Set
from collections import defaultdict

class SearchIndex:
    def __init__(self):
        self.index: Dict[str, Set[str]] = defaultdict(set)

    def _tokenize(self, text: str) -> List[str]:
        # Simple German-friendly tokenizer
        if not text:
            return []
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r'\w+', text.lower())
        # Basic German stopword list
        stopwords = {
            'der', 'die', 'das', 'und', 'in', 'zu', 'den', 'von', 'für', 'mit', 'ist', 'im', 'des', 'auf', 'nicht',
            'ein', 'eine', 'einen', 'oder', 'aber', 'auch', 'dem', 'dass', 'wenn', 'zur', 'zum'
        }
        return [t for t in tokens if len(t) > 2 and t not in stopwords]

    def add_document(self, doc_id: str, text: str):
        tokens = self._tokenize(text)
        for token in tokens:
            self.index[token].add(doc_id)

    def search(self, query: str) -> Set[str]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return set()

        results = None
        for token in query_tokens:
            token_results = set()
            # Support basic prefix matching
            for indexed_token in self.index:
                if indexed_token.startswith(token):
                    token_results.update(self.index[indexed_token])

            if results is None:
                results = token_results
            else:
                results.intersection_update(token_results)

        return results if results else set()

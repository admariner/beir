from __future__ import annotations

import logging

import numpy as np
from tqdm.autonotebook import trange

from .. import BaseSearch

logger = logging.getLogger(__name__)


class SparseSearch(BaseSearch):
    def __init__(self, model, batch_size: int = 16, **kwargs):
        self.model = model
        self.batch_size = batch_size
        self.sparse_matrix = None
        self.results = {}

    def search(
        self,
        corpus: dict[str, dict[str, str]],
        queries: dict[str, str],
        top_k: int,
        score_function: str,
        query_weights: bool = False,
        *args,
        **kwargs,
    ) -> dict[str, dict[str, float]]:
        doc_ids = list(corpus.keys())
        query_ids = list(queries.keys())
        documents = [corpus[doc_id] for doc_id in doc_ids]
        logging.info("Computing document embeddings and creating sparse matrix")
        self.sparse_matrix = self.model.encode_corpus(documents, batch_size=self.batch_size)

        logging.info("Starting to Retrieve...")
        for start_idx in trange(0, len(queries), desc="query"):
            qid = query_ids[start_idx]
            query_tokens = self.model.encode_query(queries[qid])

            if query_weights:
                # used for uniCOIL, query weights are considered!
                scores = self.sparse_matrix.dot(query_tokens)
            else:
                # used for SPARTA, query weights are not considered (i.e. binary)!
                scores = np.asarray(self.sparse_matrix[query_tokens, :].sum(axis=0)).squeeze(0)

            top_k_ind = np.argpartition(scores, -top_k)[-top_k:]
            self.results[qid] = {doc_ids[pid]: float(scores[pid]) for pid in top_k_ind if doc_ids[pid] != qid}

        return self.results

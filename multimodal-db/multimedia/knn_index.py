from __future__ import annotations

from typing import Iterable

import numpy as np

from core.metrics import IOStats, OperationResult
from core.ports.index import Index, Key, Predicate, Record


class MultimediaKNNIndex(Index):
    # Guarda histogramas en memoria indexados por clave
    def __init__(self) -> None:
        self._vectors: dict[str, np.ndarray] = {}

    def build(self, records: Iterable[Record]) -> OperationResult:
        # Cada record es una tupla (track_id, histograma)
        io = IOStats()
        count = 0
        for key, vector in records:
            self._vectors[str(key)] = np.asarray(vector, dtype=np.float32)
            count += 1
        return OperationResult(affected=count, io=io)

    def insert(self, key: Key, record: Record) -> OperationResult:
        self._vectors[str(key)] = np.asarray(record, dtype=np.float32)
        return OperationResult(affected=1)

    def search(self, predicate: Predicate, k: int | None = 10) -> OperationResult:
        # predicate es el histograma de la consulta
        query = np.asarray(predicate, dtype=np.float32)
        if len(self._vectors) == 0:
            return OperationResult(records=[])
        k = k or 10
        keys = list(self._vectors.keys())
        matrix = np.stack([self._vectors[k_] for k_ in keys])
        # Similitud coseno entre la consulta y todos los vectores
        norms = np.linalg.norm(matrix, axis=1)
        query_norm = np.linalg.norm(query)
        if query_norm == 0 or np.all(norms == 0):
            return OperationResult(records=[])
        similarities = (matrix @ query) / (norms * query_norm + 1e-9)
        top_k = int(min(k, len(keys)))
        indices = np.argpartition(similarities, -top_k)[-top_k:]
        indices = indices[np.argsort(similarities[indices])[::-1]]
        results = [(keys[i], float(similarities[i])) for i in indices]
        return OperationResult(records=results)

    def delete(self, key: Key) -> OperationResult:
        removed = self._vectors.pop(str(key), None)
        return OperationResult(affected=0 if removed is None else 1)

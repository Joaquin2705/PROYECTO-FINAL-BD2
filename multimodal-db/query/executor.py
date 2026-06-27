from __future__ import annotations

from typing import Any

from core.ports.storage import StorageEngine

from query.ports import Executor
from query.plan_types import PlanOp, QueryPlan, ResultSet
from query.index_factory import IndexFactory, IndexType


# Ejecuta los planes usando la fábrica de índices
class QueryExecutor(Executor):

    def __init__(self, factory: IndexFactory, storage: StorageEngine) -> None:
        self._factory = factory
        self._storage = storage
        # Columnas de cada tabla creada
        self._tables: dict[str, list[str]] = {}
        # Índice guardado por tabla y columna
        self._indexes: dict[tuple[str, str], Any] = {}

    def execute(self, plan: QueryPlan) -> ResultSet:
        if plan.op is PlanOp.CREATE_TABLE:
            return self._create_table(plan)
        if plan.op is PlanOp.DROP_TABLE:
            return self._drop_table(plan)
        if plan.op is PlanOp.CREATE_INDEX:
            return self._create_index(plan)
        raise ValueError(f"operación no soportada: {plan.op.name}")

    def _create_table(self, plan: QueryPlan) -> ResultSet:
        self._tables[plan.table] = list(plan.columns)
        return ResultSet()

    def _drop_table(self, plan: QueryPlan) -> ResultSet:
        self._tables.pop(plan.table, None)
        for key in [k for k in self._indexes if k[0] == plan.table]:
            del self._indexes[key]
        return ResultSet()

    def _create_index(self, plan: QueryPlan) -> ResultSet:
        index_type = IndexType.from_name(plan.index_type)
        schema = self._tables.get(plan.table, [])
        index = self._factory.create(index_type, schema, self._storage)
        self._indexes[(plan.table, plan.columns[0])] = index
        return ResultSet()

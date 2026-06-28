# Proyecto 2: Base de Datos 2

Integrantes:
- Kiara Alexandra Balcázar Santa Cruz

## Arquitectura

Interfaces (ABCs) en `multimodal-db/`:
- `core/ports/`: `StorageEngine`, `BufferManager` e `Index`.
- `core/metrics.py`: `IOStats` y `OperationResult`.
- `indices/ports.py`: tipos de `Predicate`.
- `multimedia/ports/`: `FeatureExtractor` y `Codebook`.
- `query/ports.py`: `Parser`, `Planner` y `Executor`.
- `query/plan_types.py`: `QueryPlan` y `ResultSet`.

`tests/mocks.py` trae una versión falsa de cada interface para las pruebas.

## Índices

La capa de acceso incluye B+Tree, ISAM, hash extendible, R-Tree e índice invertido con SPIMI. La documentación de complejidad y criterios de selección está en [`docs/indices.md`](docs/indices.md).

## Entorno

Python 3.12:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Las dependencias están fijadas en `requirements.txt`.

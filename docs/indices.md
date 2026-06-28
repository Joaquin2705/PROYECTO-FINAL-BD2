# Índices de la Capa de Acceso

Este documento resume los índices implementados por Dev B, sus costos esperados y el criterio de selección por tipo de operación. Todos exponen el contrato `Index`: `build`, `insert`, `search` y `delete`.

## Resumen

| Índice | Uso principal | Búsqueda puntual | Búsqueda por rango | KNN | Texto |
| --- | --- | --- | --- | --- | --- |
| B+Tree clustered | Claves ordenables y rangos frecuentes | O(log n + r) | O(log n + r) | No aplica | No aplica |
| ISAM | Datos mayormente estáticos con rangos | O(log p + o) | O(log p + r + o) | No aplica | No aplica |
| Hash extendible | Igualdad exacta en claves sin orden | O(1) esperado | O(n) | No aplica | No aplica |
| R-Tree | Puntos o rectángulos multidimensionales | O(log n) esperado | O(log n + r) esperado | O(log n + k) esperado | No aplica |
| Inverted/SPIMI | Texto y recuperación por relevancia | No aplica | No aplica | No aplica | O(\|q\| + postings(q)) |

`n` es el número de registros, `r` es el número de resultados, `p` es el número de páginas primarias, `o` es el costo de overflow y `|q|` es el número de términos de consulta.

## B+Tree Clustered

Implementación: `multimodal-db/indices/bplus_tree.py`.

Selección recomendada:

- Usar cuando la columna tenga orden total: enteros, fechas, precios o identificadores.
- Usar cuando se necesiten consultas `=`, `BETWEEN`, `<`, `<=`, `>` o `>=`.
- Preferirlo sobre hash cuando el planner deba mantener resultados ordenados o recorrer rangos.

Costos esperados:

- `build`: O(n log n), porque ordena e inserta.
- `insert`: O(log n), con split ocasional de hoja o nodo interno.
- `search` por igualdad: O(log n + r).
- `search` por rango: O(log n + r), porque las hojas están enlazadas.
- `delete`: O(log n + r) en la versión actual, eliminando el grupo de clave.

Notas:

- Agrupa duplicados bajo una misma clave.
- El split de hojas evita cortar duplicados en la frontera.
- Es buen candidato para índices primarios o clustered.

## ISAM

Implementación: `multimodal-db/indices/isam.py`.

Selección recomendada:

- Usar cuando el dataset sea estable y las cargas se hagan en lote.
- Usar para rangos sobre claves ordenables cuando las inserciones posteriores sean moderadas.
- Evitarlo si habrá muchas inserciones dinámicas, porque el overflow puede crecer y degradar el rendimiento.

Costos esperados:

- `build`: O(n log n), por ordenamiento inicial.
- `insert`: O(log p + o), porque ubica página primaria y puede recorrer overflow.
- `search` por igualdad: O(log p + o + r).
- `search` por rango: O(log p + r + o).
- `delete`: O(log p + o), eliminando en primaria y overflow.

Notas:

- Las páginas primarias son estáticas después del build.
- Las inserciones tardías van a overflow pages.
- Es útil para explicar el trade-off entre carga estática y costo de mantenimiento.

## Hash Extendible

Implementación: `multimodal-db/indices/extendible_hash.py`.

Selección recomendada:

- Usar para consultas de igualdad exacta.
- Usar cuando la clave no necesita orden.
- Evitarlo para rangos, porque no preserva cercanía entre claves.

Costos esperados:

- `build`: O(n) esperado.
- `insert`: O(1) esperado, con split de bucket cuando se llena.
- `search` por igualdad: O(1) esperado.
- `search` por rango: O(n), solo como fallback de contrato.
- `delete`: O(1) esperado.

Notas:

- Maneja `global_depth`, `local_depth` y duplicación de directorio.
- Los duplicados se guardan en el mismo bucket lógico.
- Es la mejor opción para filtros `WHERE key = value` sin ordenamiento.

## R-Tree

Implementación: `multimodal-db/indices/rtree.py`.

Selección recomendada:

- Usar para puntos, coordenadas, bounding boxes o vectores espaciales de baja dimensión.
- Usar para `SpatialRangePredicate`.
- Usar para `KnnPredicate` cuando la consulta sea geométrica.

Costos esperados:

- `build`: O(n log n) esperado.
- `insert`: O(log n) esperado.
- `search` espacial por rango: O(log n + r) esperado.
- `search` KNN: O(log n + k) esperado.
- `delete`: O(log n + r) esperado.

Notas:

- Usa la librería `rtree`, declarada en `requirements.txt`.
- La clase propia envuelve la librería para cumplir el contrato `Index`.
- Mantiene los records en el adaptador y usa el índice espacial para ids internos.

## Inverted Index con SPIMI

Implementación:

- `multimodal-db/indices/inverted/spimi_builder.py`
- `multimodal-db/indices/inverted/text_index.py`
- `multimodal-db/indices/inverted/text_preprocessor.py`

Selección recomendada:

- Usar para texto libre, letras, descripciones o chunks textuales.
- Usar para `TextMatchPredicate`.
- Usar cuando se necesite ranking por relevancia y no solo coincidencia exacta.

Costos esperados:

- `build`: O(T log b), donde `T` es el total de tokens y `b` el número de bloques SPIMI.
- Merge k-way: O(V log b), donde `V` es el total de términos emitidos por bloques.
- `insert`: O(t), donde `t` es el número de tokens del documento.
- `search`: O(|q| + postings(q)).
- Ranking TF-IDF: O(postings(q)).
- `delete`: O(V), porque limpia el documento de todas las listas.

Notas:

- Usa SPIMI por bloques y merge k-way con heap.
- Usa preprocesamiento con stopwords y stemming mediante NLTK cuando está disponible.
- Persiste postings en páginas del `StorageEngine` como líneas JSON, sin `pickle`.
- Calcula normas de documento para similitud coseno TF-IDF.

## Criterio de Selección

| Pregunta del planner | Índice recomendado |
| --- | --- |
| ¿La consulta es igualdad exacta y no requiere orden? | Hash extendible |
| ¿La consulta necesita rangos ordenados? | B+Tree clustered |
| ¿El dataset es estático y se consulta por rangos? | ISAM |
| ¿La consulta usa coordenadas o ventanas espaciales? | R-Tree |
| ¿La consulta pide vecinos más cercanos espaciales? | R-Tree |
| ¿La consulta es texto libre con relevancia? | Inverted/SPIMI |
| ¿Se necesita comparar el motor propio contra PostgreSQL GIN? | Inverted/SPIMI |

## Relación con el Proyecto

El enunciado pide un sistema multimodal basado en `split -> feature extraction -> codebook -> inverted index`. Por eso el índice invertido es el índice central para texto y para histogramas de codewords. Los demás índices cumplen la capa de acceso del motor y permiten comparar estrategias clásicas de organización de archivos vistas en Base de Datos 2.

Para la evaluación experimental, cada índice debe reportar sus métricas mediante `OperationResult` e `IOStats`. Cuando Dev A integre `BufferManager`, los accesos a disco deben venir de esa capa y no de contadores internos de cada índice.

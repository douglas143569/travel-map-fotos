# Integração de GeoJSON dos estados (UF) no projeto

## Objetivo
Substituir o MVP atual (marcadores) por um mapa com **polígonos clicáveis** dos estados do Brasil.

## Passos
1. Adicionar arquivo `static/geo/uf-br.geojson` (GeoJSON das 27 UFs).
2. Atualizar `static/js/app.js` para carregar o GeoJSON via `fetch` e renderizar com `L.geoJSON`.
3. No clique do estado, chamar `showPhotosForState(estado)`.
4. Ajustar `templates/index.html` se necessário.
5. Testar no navegador.


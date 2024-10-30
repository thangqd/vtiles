const { exec } = require('child_process');

function parseResponse(response) {
    let parsedData = {};
  
    try {
      // Basic check for valid JSON structure (optional)
      if (!response.trim().startsWith('{') && !response.trim().startsWith('[')) {
        throw new SyntaxError("Response does not start with a valid JSON structure");
      }
  
      // Convert Python-style literals to JavaScript-compatible ones
      let jsonCompatibleText = response
        .replace(/\bTrue\b/g, 'true')
        .replace(/\bFalse\b/g, 'false')
        .replace(/\bNone\b/g, 'null');
  
      // Attempt to parse JSON
      let data = JSON.parse(jsonCompatibleText);
  
      // Extract data with safe fallbacks
      parsedData.addressedTilesCount = data.addressed_tiles_count || 0;
      parsedData.center = {
        lat: (data.center_lat_e7 || 0) / 1e7,
        lon: (data.center_lon_e7 || 0) / 1e7,
        zoom: data.center_zoom || 0
      };
      parsedData.compression = data.internal_compression || 'N/A';
      parsedData.maxZoom = data.max_zoom || 'N/A';
      parsedData.metadata = {
        length: data.metadata_length || 0,
        offset: data.metadata_offset || 0
      };
  
      parsedData.tileData = {
        count: data.tile_contents_count || 0,
        entriesCount: data.tile_entries_count || 0,
        dataLength: data.tile_data_length || 0,
        dataOffset: data.tile_data_offset || 0
      };
  
      parsedData.vectorLayers = (data.vector_layers || []).map(layer => ({
        id: layer.id || 'N/A',
        minzoom: layer.minzoom || 0,
        maxzoom: layer.maxzoom || 0,
        fields: layer.fields || {}
      }));
  
    } catch (error) {
      console.error("Error parsing response:", error);
      console.error("Raw response for debugging:", response); // Log raw response to diagnose
      parsedData.error = "Failed to parse response data.";
    }
  
    return parsedData;
  }
  
  exec('pmtilesinfo vietnam.pmtiles', (error, stdout, stderr) => {
    if (error) {
        console.error(`Error: ${error.message}`);
        return;
    }
    if (stderr) {
        console.error(`Stderr: ${stderr}`);
        return;
    }

    // Parse the JSON output
      // Parse and output JSON
    const jsonData = parseResponse(stdout);
  
    const pmtilesInfo = JSON.parse(jsonData);

    // Extract vector_layers
    const vectorLayers = pmtilesInfo['vector_layers'];

    // Generate MapLibre layers configuration
    const mapLayers = vectorLayers.map(layer => {
        let paint = {};
        let type = 'fill'; // Default type

        // Determine the layer type based on common field names or other heuristics
        if (layer.fields.hasOwnProperty('kind') || layer.fields.hasOwnProperty('sort_rank')) {
            type = 'line';
            paint = {
                'line-color': '#888888',
                'line-width': 2
            };
        } else if (layer.fields.hasOwnProperty('height') || layer.fields.hasOwnProperty('min_height')) {
            type = 'fill';
            paint = {
                'fill-color': '#888888',
                'fill-opacity': 0.5
            };
        } else if (layer.fields.hasOwnProperty('name') || layer.fields.hasOwnProperty('population')) {
            type = 'symbol';
            paint = {
                'text-color': '#888888'
            };
        } else {
            type = 'fill';
            paint = {
                'fill-color': '#888888',
                'fill-opacity': 0.5
            };
        }

        return {
            id: `${layer.id}_layer`,
            type,
            source: 'example_source',
            'source-layer': layer.id,
            paint
        };
    });

    console.log('MapLibre Layers:', mapLayers);

    // Optionally, save the layers configuration to a file
    const fs = require('fs');
    fs.writeFileSync('layers.json', JSON.stringify(mapLayers, null, 2));
});

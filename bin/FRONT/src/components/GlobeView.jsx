import { useEffect, useMemo, useState } from 'react';
import Globe from 'react-globe.gl';
import { Box } from '@mui/material';
import { CONTINENT_COLORS, getContinentFromFeature } from '../utils/continent';

const earthTexture = '//unpkg.com/three-globe/example/img/earth-night.jpg';
const bumpTexture = '//unpkg.com/three-globe/example/img/earth-topology.png';
const countriesGeoJsonUrl = 'https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson';

const CONTINENT_CAP_COLORS = {
  Asia: 'rgba(0,240,255,0.6)',
  Europe: 'rgba(122,0,255,0.6)',
  'North America': 'rgba(255,0,200,0.6)',
  'South America': 'rgba(255,122,0,0.6)',
  Africa: 'rgba(0,255,156,0.6)',
  Oceania: 'rgba(0,140,255,0.6)',
  Unknown: 'rgba(138,149,179,0.4)',
};

function GlobeView({ rows, selectedContinent, onContinentClick }) {
  const [geoFeatures, setGeoFeatures] = useState([]);

  useEffect(() => {
    let active = true;

    const loadGeo = async () => {
      try {
        const response = await fetch(countriesGeoJsonUrl);
        const geoJson = await response.json();
        if (!active || !Array.isArray(geoJson?.features)) return;

        const enhanced = geoJson.features.map((feature) => ({
          ...feature,
          properties: {
            ...feature.properties,
            continent: getContinentFromFeature(feature),
          },
        }));
        setGeoFeatures(enhanced);
      } catch {
        setGeoFeatures([]);
      }
    };

    loadGeo();

    return () => {
      active = false;
    };
  }, []);

  const countsByContinent = useMemo(() => {
    return (rows || []).reduce((acc, row) => {
      const continent = row.continent || 'Unknown';
      acc[continent] = (acc[continent] || 0) + 1;
      return acc;
    }, {});
  }, [rows]);

  const polygonsData = useMemo(
    () =>
      geoFeatures.map((feature) => {
        const continent = feature?.properties?.continent || 'Unknown';
        return {
          ...feature,
          properties: {
            ...feature.properties,
            continent,
            authorCount: countsByContinent[continent] || 0,
          },
        };
      }),
    [geoFeatures, countsByContinent]
  );

  return (
    <Box className="globe-wrap">
      <Globe
        globeImageUrl={earthTexture}
        bumpImageUrl={bumpTexture}
        backgroundColor="rgba(0,0,0,0)"
        polygonsData={polygonsData}
        polygonCapColor={(d) => {
          const continent = d?.properties?.continent || 'Unknown';
          const baseColor = CONTINENT_CAP_COLORS[continent] || CONTINENT_CAP_COLORS.Unknown;
          if (!selectedContinent) return baseColor;
          return continent === selectedContinent ? baseColor : 'rgba(30,35,58,0.18)';
        }}
        polygonSideColor={() => 'rgba(0,0,0,0)'}
        polygonStrokeColor={(d) => {
          const continent = d?.properties?.continent || 'Unknown';
          if (selectedContinent && continent !== selectedContinent) {
            return 'rgba(100,110,160,0.2)';
          }
          return CONTINENT_COLORS[continent] || CONTINENT_COLORS.Unknown;
        }}
        polygonAltitude={(d) => {
          const continent = d?.properties?.continent || 'Unknown';
          return selectedContinent && continent === selectedContinent ? 0.02 : 0.01;
        }}
        polygonsTransitionDuration={700}
        polygonLabel={(d) => `
          <div class="globe-tooltip">
            <strong>Continent: ${d?.properties?.continent || 'Unknown'}</strong><br />
            Authors: ${d?.properties?.authorCount || 0}
          </div>
        `}
        onPolygonClick={(polygon) => onContinentClick?.(polygon?.properties?.continent || 'Unknown')}
      />
    </Box>
  );
}

export default GlobeView;

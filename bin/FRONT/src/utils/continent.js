export const CONTINENT_COLORS = {
  Asia: '#00f0ff',
  Europe: '#7a00ff',
  'North America': '#ff00c8',
  'South America': '#ff7a00',
  Africa: '#00ff9c',
  Oceania: '#008cff',
  Unknown: '#8a95b3',
};

export const CONTINENT_CENTERS = {
  Asia: { lat: 34, lng: 100 },
  Europe: { lat: 54, lng: 15 },
  'North America': { lat: 45, lng: -100 },
  'South America': { lat: -15, lng: -60 },
  Africa: { lat: 1, lng: 20 },
  Oceania: { lat: -25, lng: 135 },
  Unknown: { lat: 0, lng: 0 },
};

const COUNTRY_TO_CONTINENT = {
  Thailand: 'Asia',
  USA: 'North America',
  'United States': 'North America',
  UK: 'Europe',
  'United Kingdom': 'Europe',
  Japan: 'Asia',
  India: 'Asia',
  Germany: 'Europe',
  Brazil: 'South America',
  Canada: 'North America',
  Mexico: 'North America',
  France: 'Europe',
  Spain: 'Europe',
  Italy: 'Europe',
  China: 'Asia',
  Singapore: 'Asia',
  Australia: 'Oceania',
  'New Zealand': 'Oceania',
  Nigeria: 'Africa',
  Kenya: 'Africa',
  Egypt: 'Africa',
  Argentina: 'South America',
  Chile: 'South America',
  Colombia: 'South America',
  Russia: 'Europe',
  Kazakhstan: 'Asia',
  Turkey: 'Europe',
  'South Korea': 'Asia',
  Korea: 'Asia',
  Vietnam: 'Asia',
  Indonesia: 'Asia',
  Philippines: 'Asia',
  Pakistan: 'Asia',
  Bangladesh: 'Asia',
  Sweden: 'Europe',
  Norway: 'Europe',
  Finland: 'Europe',
  Poland: 'Europe',
  Netherlands: 'Europe',
  Belgium: 'Europe',
  Portugal: 'Europe',
  Switzerland: 'Europe',
  Austria: 'Europe',
  Denmark: 'Europe',
  Ireland: 'Europe',
  Greenland: 'North America',
  Peru: 'South America',
  Uruguay: 'South America',
  Venezuela: 'South America',
  Ecuador: 'South America',
  Morocco: 'Africa',
  Algeria: 'Africa',
  Tunisia: 'Africa',
  'South Africa': 'Africa',
  Ethiopia: 'Africa',
  Ghana: 'Africa',
  Tanzania: 'Africa',
  Madagascar: 'Africa',
};

const COUNTRY_ALIASES = {
  'United States of America': 'United States',
  'Russian Federation': 'Russia',
  'Korea, Republic of': 'South Korea',
  'Korea (Rep.)': 'South Korea',
  'Viet Nam': 'Vietnam',
  'United Republic of Tanzania': 'Tanzania',
  'Dem. Rep. Congo': 'Unknown',
  'Congo (Kinshasa)': 'Unknown',
  "Cote d'Ivoire": 'Unknown',
  'Bosnia and Herz.': 'Unknown',
};

export const getContinentFromCountry = (country) => {
  if (!country) return 'Unknown';
  const normalized = COUNTRY_ALIASES[country] || country;
  return COUNTRY_TO_CONTINENT[normalized] || 'Unknown';
};

export const getCountryNameFromFeature = (feature) => {
  const properties = feature?.properties || {};
  return (
    properties.ADMIN ||
    properties.admin ||
    properties.NAME ||
    properties.name ||
    properties.COUNTRY ||
    properties.country ||
    properties.SOVEREIGNT ||
    null
  );
};

export const getContinentFromFeature = (feature) => {
  const countryName = getCountryNameFromFeature(feature);
  return getContinentFromCountry(countryName);
};

export const normalizeRowContinent = (row) => {
  const continent = row.continent || getContinentFromCountry(row.country);
  return { ...row, continent };
};

export const aggregateByContinent = (rows) => {
  const grouped = rows.reduce((acc, row) => {
    const continent = row.continent || getContinentFromCountry(row.country);
    acc[continent] = (acc[continent] || 0) + 1;
    return acc;
  }, {});

  return Object.entries(grouped).map(([continent, count]) => {
    const center = CONTINENT_CENTERS[continent] || CONTINENT_CENTERS.Unknown;
    return {
      continent,
      count,
      lat: center.lat,
      lng: center.lng,
      color: CONTINENT_COLORS[continent] || CONTINENT_COLORS.Unknown,
    };
  });
};

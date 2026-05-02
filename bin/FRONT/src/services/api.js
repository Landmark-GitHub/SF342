import axios from 'axios';
import { aggregateByContinent, normalizeRowContinent } from '../utils/continent';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
});

export const uploadCsv = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const ingestData = async () => {
  const { data } = await api.post('/ingest');
  return data;
};

export const fetchGlobeData = async () => {
  const { data } = await api.get('/globe');
  if (!Array.isArray(data)) return [];

  if (data[0]?.continent) {
    return data;
  }

  if (data[0]?.country) {
    const normalized = data.map((item) => normalizeRowContinent(item));
    return aggregateByContinent(normalized);
  }

  return data;
};

export const fetchTableData = async (country) => {
  const { data } = await api.get('/table', {
    params: country ? { country } : undefined,
  });
  if (!Array.isArray(data)) return [];
  return data.map((row) => normalizeRowContinent(row));
};

export const fetchDemoData = async () => {
  const response = await fetch('/metadata.json');
  if (!response.ok) {
    throw new Error('Unable to load demo metadata.');
  }
  const raw = await response.json();

  const tableRaw = Array.isArray(raw.table) ? raw.table : [];
  const table = tableRaw.map((row) => normalizeRowContinent(row));
  const globe = aggregateByContinent(table);

  return { globe, table };
};

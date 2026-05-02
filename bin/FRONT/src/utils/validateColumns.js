const REQUIRED_COLUMNS = ['author_name', 'l1_field', 'l2_domain', 'subfield_name', 'expertise_score', 'paper_count'];

export const validateColumns = async (file) => {
  const text = await file.text();
  const firstLine = text.split(/\r?\n/).find((line) => line.trim().length > 0);

  if (!firstLine) {
    throw new Error('CSV file appears to be empty.');
  }

  const columns = firstLine
    .split(',')
    .map((item) => item.trim().replace(/^"|"$/g, ''))
    .filter(Boolean);

  const missing = REQUIRED_COLUMNS.filter((column) => !columns.includes(column));
  if (missing.length) {
    throw new Error(`Missing required columns: ${missing.join(', ')}`);
  }

  return true;
};

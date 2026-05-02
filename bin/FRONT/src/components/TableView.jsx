import { Box, Chip, Tooltip, LinearProgress, Typography } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';

// ===== SIMILARITY (Minimal Gold) =====
const renderSimilarity = (value) => {
  if (value == null) return '-';

  const percent = value * 100;

  return (
    <Box sx={{ width: '100%' }}>
      <LinearProgress
        variant="determinate"
        value={percent}
        sx={{
          height: 4,
          borderRadius: 2,
          backgroundColor: 'rgba(255,255,255,0.06)',
          '& .MuiLinearProgress-bar': {
            backgroundColor: '#D4AF37',
          },
        }}
      />
      <Typography
        sx={{
          fontSize: 11,
          mt: 0.5,
          color: '#999',
          fontFamily: 'Inter',
        }}
      >
        {percent.toFixed(1)}%
      </Typography>
    </Box>
  );
};

// ===== COLUMNS =====
const columns = [
  {
    field: 'author_name',
    headerName: 'Author',
    flex: 1.5,
    minWidth: 220,
  },
  {
    field: 'l1_field',
    headerName: 'Field',
    flex: 1,
    minWidth: 160,
    renderCell: (params) => (
      <Chip
        label={params.value}
        size="small"
        sx={{
          backgroundColor: 'rgba(255,255,255,0.05)',
          color: '#F4F4F4',
          borderRadius: '6px',
          fontSize: 11,
          fontFamily: 'Inter',
        }}
      />
    ),
  },
  {
    field: 'l2_domain',
    headerName: 'Domain',
    flex: 1.2,
    minWidth: 180,
    renderCell: (params) => (
      <Tooltip title={params.value}>
        <span className="ellipsis">{params.value}</span>
      </Tooltip>
    ),
  },
  {
    field: 'subfield_name',
    headerName: 'Subfield',
    flex: 1.4,
    minWidth: 200,
    renderCell: (params) => (
      <Tooltip title={params.value}>
        <span className="ellipsis">{params.value}</span>
      </Tooltip>
    ),
  },
  {
    field: 'expertise_score',
    headerName: 'Expertise',
    flex: 0.8,
    minWidth: 120,
    renderCell: (params) => (
      <Typography
        sx={{
          color: '#D4AF37',
          fontWeight: 500,
          fontFamily: 'Inter',
        }}
      >
        {params.value}
      </Typography>
    ),
  },
  {
    field: 'paper_count',
    headerName: 'Papers',
    flex: 0.7,
    minWidth: 100,
  },
  {
    field: 'avg_similarity',
    headerName: 'Similarity',
    flex: 1,
    minWidth: 160,
    renderCell: (params) => renderSimilarity(params.value),
  },
  {
    field: 'first_author_papers',
    headerName: '1st',
    flex: 0.5,
    minWidth: 80,
  },
  {
    field: 'corresponding_papers',
    headerName: 'Corr',
    flex: 0.6,
    minWidth: 90,
  },
  {
    field: 'author_papers',
    headerName: 'Total',
    flex: 0.6,
    minWidth: 90,
  },
];

// ===== MAIN TABLE =====
function TableView({ rows, selectedCountry, selectedContinent, onRowClick }) {
  const safeRows = (rows || []).map((row, index) => ({
    id: row.id || `${row.author_id}-${index}`,
    ...row,
  }));

  return (
    <Box
      sx={{
        height: 600,
        width: '100%',
        backgroundColor: '#1A1A1A',
        borderRadius: 3,
        px: 2,
        py: 2,
      }}
    >
      {/* HEADLINE */}
      <Typography
        sx={{
          fontFamily: 'Playfair Display',
          fontSize: 20,
          color: '#F4F4F4',
          mb: 2,
          letterSpacing: 0.5,
        }}
      >
        Research Expertise
      </Typography>

      <DataGrid
        rows={safeRows}
        columns={columns}
        pageSizeOptions={[10, 25, 50]}
        initialState={{
          pagination: { paginationModel: { pageSize: 10, page: 0 } },
        }}
        disableColumnMenu
        onRowClick={(params) => onRowClick?.(params.row)}
        sx={{
          color: '#F4F4F4',
          border: 'none',
          fontFamily: 'Inter',

          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: 'transparent',
            borderBottom: '1px solid rgba(255,255,255,0.08)',
            fontWeight: 400,
            color: '#aaa',
          },

          '& .MuiDataGrid-cell': {
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            paddingTop: '14px',
            paddingBottom: '14px',
          },

          '& .MuiDataGrid-row': {
            cursor: 'pointer',
            transition: 'background 0.2s ease',
            '&:hover': {
              backgroundColor: 'rgba(255,255,255,0.04)',
            },
          },

          '& .MuiDataGrid-footerContainer': {
            borderTop: '1px solid rgba(255,255,255,0.08)',
          },
        }}
      />

      {/* FILTER TAG */}
      <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
        {selectedContinent && (
          <Chip
            label={selectedContinent}
            sx={{
              backgroundColor: 'rgba(255,255,255,0.05)',
              color: '#F4F4F4',
            }}
          />
        )}
        {selectedCountry && (
          <Chip
            label={selectedCountry}
            sx={{
              backgroundColor: '#D4AF37',
              color: '#0D0D0D',
            }}
          />
        )}
      </Box>
    </Box>
  );
}

export default TableView;
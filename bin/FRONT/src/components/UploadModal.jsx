import { useState } from 'react';
import { Alert, Box, Button, Dialog, DialogContent, DialogTitle, Stack, Typography } from '@mui/material';
import { uploadCsv, ingestData } from '../services/api';
import { validateColumns } from '../utils/validateColumns';

function UploadModal({ open, onClose, onUploadSuccess, timingOnly = false, uploadTime }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file first.');
      return;
    }

    try {
      setBusy(true);
      setError('');
      await validateColumns(file);
      const start = performance.now();
      await uploadCsv(file);
      await ingestData();
      const seconds = (performance.now() - start) / 1000;
      onClose?.();
      onUploadSuccess?.(seconds);
      setFile(null);
    } catch (err) {
      setError(err?.message || 'Upload failed.');
    } finally {
      setBusy(false);
    }
  };

  if (timingOnly) {
    return (
      <Dialog open={open} onClose={onClose} PaperProps={{ className: 'glass-modal timing-modal' }}>
        <DialogTitle className="modal-title">Upload Success</DialogTitle>
        <DialogContent>
          <Typography className="timing-text">Processing Time: {(uploadTime || 0).toFixed(2)} seconds</Typography>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" PaperProps={{ className: 'glass-modal' }}>
      <DialogTitle className="modal-title">Upload CSV</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <Box className="upload-box">
            <input
              type="file"
              accept=".csv"
              onChange={(event) => {
                setFile(event.target.files?.[0] || null);
              }}
            />
          </Box>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <Stack direction="row" spacing={1.5} justifyContent="flex-end">
            <Button className="neon-btn ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button className="neon-btn" onClick={handleUpload} disabled={busy}>
              {busy ? 'Uploading...' : 'Start Upload'}
            </Button>
          </Stack>
        </Stack>
      </DialogContent>
    </Dialog>
  );
}

export default UploadModal;

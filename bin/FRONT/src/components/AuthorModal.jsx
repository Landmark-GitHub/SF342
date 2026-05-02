import { Box, Chip, Dialog, DialogContent, DialogTitle, Stack, Typography } from '@mui/material';

function AuthorModal({ open, author, onClose }) {
  if (!author) return null;

  const papers = author.papers || [];
  const fields = [author.l1_field, author.l2_domain, author.subfield_name].filter(Boolean);

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md" PaperProps={{ className: 'glass-modal' }}>
      <DialogTitle className="modal-title">{author.author_name}</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <Box>
            <Typography className="label">Fields</Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {fields.map((field) => (
                <Chip key={field} label={field} className="neon-chip" />
              ))}
            </Stack>
          </Box>
          <Box>
            <Typography className="label">Paper List</Typography>
            {papers.length ? (
              <ul className="paper-list">
                {papers.map((paper, idx) => (
                  <li key={`${paper}-${idx}`}>{paper}</li>
                ))}
              </ul>
            ) : (
              <Typography color="text.secondary">No papers available.</Typography>
            )}
          </Box>
        </Stack>
      </DialogContent>
    </Dialog>
  );
}

export default AuthorModal;

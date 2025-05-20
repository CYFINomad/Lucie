import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import { motion } from 'framer-motion';

const UrlLearningPanel = ({ urls, onAdd, onEdit, onDelete, onProcess }) => {
  const { theme } = useTheme();
  const [newUrl, setNewUrl] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedUrl, setSelectedUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  const handleAddUrl = async () => {
    if (!newUrl) return;

    try {
      setIsProcessing(true);
      setError('');
      await onAdd(newUrl);
      setNewUrl('');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleEditUrl = async (url) => {
    setSelectedUrl(url);
    setIsDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedUrl) return;

    try {
      setIsProcessing(true);
      setError('');
      await onEdit(selectedUrl);
      setIsDialogOpen(false);
      setSelectedUrl(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleProcessUrl = async (url) => {
    try {
      setIsProcessing(true);
      setError('');
      await onProcess(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 3,
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Typography variant="h6" gutterBottom>
          URL Learning Sources
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box display="flex" gap={1} mb={3}>
          <TextField
            fullWidth
            label="Add URL"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="https://example.com"
            disabled={isProcessing}
          />
          <Button
            variant="contained"
            onClick={handleAddUrl}
            disabled={!newUrl || isProcessing}
            startIcon={isProcessing ? <CircularProgress size={20} /> : <AddIcon />}
          >
            Add
          </Button>
        </Box>

        <List>
          {urls.map((url) => (
            <ListItem
              key={url.id}
              sx={{
                mb: 1,
                backgroundColor: theme.palette.background.default,
                borderRadius: 1,
              }}
            >
              <ListItemText
                primary={url.url}
                secondary={
                  <Box mt={1}>
                    <Chip
                      size="small"
                      label={url.status}
                      color={url.status === 'processed' ? 'success' : 'default'}
                      sx={{ mr: 1 }}
                    />
                    {url.lastProcessed && (
                      <Typography variant="caption" color="text.secondary">
                        Last processed: {new Date(url.lastProcessed).toLocaleString()}
                      </Typography>
                    )}
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  onClick={() => handleEditUrl(url)}
                  disabled={isProcessing}
                  sx={{ mr: 1 }}
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  edge="end"
                  onClick={() => onDelete(url.id)}
                  disabled={isProcessing}
                  sx={{ mr: 1 }}
                >
                  <DeleteIcon />
                </IconButton>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => handleProcessUrl(url)}
                  disabled={isProcessing || url.status === 'processing'}
                >
                  {url.status === 'processing' ? (
                    <CircularProgress size={20} />
                  ) : (
                    'Process'
                  )}
                </Button>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>

        <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)}>
          <DialogTitle>Edit URL</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="URL"
              value={selectedUrl?.url || ''}
              onChange={(e) =>
                setSelectedUrl((prev) => ({ ...prev, url: e.target.value }))
              }
              margin="normal"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setIsDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSaveEdit} color="primary">
              Save
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </motion.div>
  );
};

export default UrlLearningPanel;

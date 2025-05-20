import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Grid,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import { motion } from 'framer-motion';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

const AgentManager = ({ agents, onCreate, onEdit, onDelete, onDuplicate }) => {
  const { theme } = useTheme();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  const initialAgentState = {
    name: '',
    description: '',
    type: 'general',
    capabilities: [],
    config: {
      memoryLimit: 512,
      priority: 'normal',
      maxConcurrentTasks: 5,
    },
  };

  const [agentData, setAgentData] = useState(initialAgentState);

  const handleOpenDialog = (agent = null) => {
    if (agent) {
      setSelectedAgent(agent);
      setAgentData(agent);
    } else {
      setSelectedAgent(null);
      setAgentData(initialAgentState);
    }
    setIsDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setSelectedAgent(null);
    setAgentData(initialAgentState);
  };

  const handleSave = async () => {
    try {
      setIsProcessing(true);
      setError('');

      if (selectedAgent) {
        await onEdit(selectedAgent.id, agentData);
      } else {
        await onCreate(agentData);
      }

      handleCloseDialog();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async (agent) => {
    try {
      setIsProcessing(true);
      setError('');
      await onDelete(agent.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDuplicate = async (agent) => {
    try {
      setIsProcessing(true);
      setError('');
      await onDuplicate(agent);
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
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">Agent Management</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Create Agent
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {agents.map((agent) => (
            <Grid item xs={12} md={6} lg={4} key={agent.id}>
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  backgroundColor: theme.palette.background.default,
                  height: '100%',
                }}
              >
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">{agent.name}</Typography>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => handleDuplicate(agent)}
                      disabled={isProcessing}
                    >
                      <ContentCopyIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(agent)}
                      disabled={isProcessing}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(agent)}
                      disabled={isProcessing}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {agent.description}
                </Typography>

                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Type: {agent.type}
                  </Typography>
                  <Typography variant="subtitle2" gutterBottom>
                    Capabilities:
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {agent.capabilities.map((capability) => (
                      <Chip
                        key={capability}
                        label={capability}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Dialog
          open={isDialogOpen}
          onClose={handleCloseDialog}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            {selectedAgent ? 'Edit Agent' : 'Create New Agent'}
          </DialogTitle>
          <DialogContent>
            <Box mt={2}>
              <TextField
                fullWidth
                label="Name"
                value={agentData.name}
                onChange={(e) =>
                  setAgentData((prev) => ({ ...prev, name: e.target.value }))
                }
                margin="normal"
              />

              <TextField
                fullWidth
                label="Description"
                value={agentData.description}
                onChange={(e) =>
                  setAgentData((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                margin="normal"
                multiline
                rows={3}
              />

              <FormControl fullWidth margin="normal">
                <InputLabel>Type</InputLabel>
                <Select
                  value={agentData.type}
                  onChange={(e) =>
                    setAgentData((prev) => ({ ...prev, type: e.target.value }))
                  }
                >
                  <MenuItem value="general">General</MenuItem>
                  <MenuItem value="specialized">Specialized</MenuItem>
                  <MenuItem value="learning">Learning</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Capabilities (comma-separated)"
                value={agentData.capabilities.join(', ')}
                onChange={(e) =>
                  setAgentData((prev) => ({
                    ...prev,
                    capabilities: e.target.value
                      .split(',')
                      .map((cap) => cap.trim())
                      .filter(Boolean),
                  }))
                }
                margin="normal"
                helperText="Enter capabilities separated by commas"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              onClick={handleSave}
              color="primary"
              disabled={isProcessing || !agentData.name}
            >
              {isProcessing ? (
                <CircularProgress size={24} />
              ) : selectedAgent ? (
                'Save Changes'
              ) : (
                'Create Agent'
              )}
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </motion.div>
  );
};

export default AgentManager;

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
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
  Alert,
  CircularProgress,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import { motion } from 'framer-motion';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import SettingsIcon from '@mui/icons-material/Settings';

const AgentDeployment = ({ agents, onDeploy, onStop, onConfigure }) => {
  const { theme } = useTheme();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false);
  const [config, setConfig] = useState({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  const handleDeploy = async (agent) => {
    try {
      setIsProcessing(true);
      setError('');
      await onDeploy(agent);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStop = async (agent) => {
    try {
      setIsProcessing(true);
      setError('');
      await onStop(agent);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfigure = (agent) => {
    setSelectedAgent(agent);
    setConfig(agent.config || {});
    setIsConfigDialogOpen(true);
  };

  const handleSaveConfig = async () => {
    if (!selectedAgent) return;

    try {
      setIsProcessing(true);
      setError('');
      await onConfigure(selectedAgent.id, config);
      setIsConfigDialogOpen(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const AgentCard = ({ agent }) => (
    <Card
      sx={{
        height: '100%',
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
      }}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{agent.name}</Typography>
          <Chip
            label={agent.status}
            color={agent.status === 'running' ? 'success' : 'default'}
            size="small"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          {agent.description}
        </Typography>

        <Box mt={2}>
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

        <Box mt={3} display="flex" gap={1}>
          <Button
            variant="contained"
            color={agent.status === 'running' ? 'error' : 'primary'}
            onClick={() =>
              agent.status === 'running'
                ? handleStop(agent)
                : handleDeploy(agent)
            }
            disabled={isProcessing}
            startIcon={
              isProcessing ? (
                <CircularProgress size={20} />
              ) : agent.status === 'running' ? (
                <StopIcon />
              ) : (
                <PlayArrowIcon />
              )
            }
          >
            {agent.status === 'running' ? 'Stop' : 'Deploy'}
          </Button>
          <Button
            variant="outlined"
            onClick={() => handleConfigure(agent)}
            disabled={isProcessing}
            startIcon={<SettingsIcon />}
          >
            Configure
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

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
          Agent Deployment
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {agents.map((agent) => (
            <Grid item xs={12} md={6} lg={4} key={agent.id}>
              <AgentCard agent={agent} />
            </Grid>
          ))}
        </Grid>

        <Dialog
          open={isConfigDialogOpen}
          onClose={() => setIsConfigDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Configure Agent</DialogTitle>
          <DialogContent>
            <Box mt={2}>
              <TextField
                fullWidth
                label="Memory Limit (MB)"
                type="number"
                value={config.memoryLimit || ''}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    memoryLimit: parseInt(e.target.value),
                  }))
                }
                margin="normal"
              />

              <FormControl fullWidth margin="normal">
                <InputLabel>Priority Level</InputLabel>
                <Select
                  value={config.priority || 'normal'}
                  onChange={(e) =>
                    setConfig((prev) => ({
                      ...prev,
                      priority: e.target.value,
                    }))
                  }
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="normal">Normal</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Max Concurrent Tasks"
                type="number"
                value={config.maxConcurrentTasks || ''}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    maxConcurrentTasks: parseInt(e.target.value),
                  }))
                }
                margin="normal"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setIsConfigDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleSaveConfig}
              color="primary"
              disabled={isProcessing}
            >
              Save Configuration
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </motion.div>
  );
};

export default AgentDeployment;

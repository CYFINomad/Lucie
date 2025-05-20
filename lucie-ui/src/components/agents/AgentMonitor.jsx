import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import { motion } from 'framer-motion';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const AgentMonitor = ({ agents, onRefresh, onViewDetails }) => {
  const { theme } = useTheme();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      setError('');
      await onRefresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleViewDetails = (agent) => {
    setSelectedAgent(agent);
    setIsDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setIsDetailsOpen(false);
    setSelectedAgent(null);
  };

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status.toLowerCase()) {
      case 'active':
        return <CheckCircleIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'error':
        return <ErrorIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const StatCard = ({ title, value, icon, color, tooltip }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={1}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {title}
          </Typography>
          {tooltip && (
            <Tooltip title={tooltip}>
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
        <Box display="flex" alignItems="center">
          {icon}
          <Typography variant="h4" component="div" sx={{ ml: 1 }}>
            {value}
          </Typography>
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
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">Agent Monitoring</Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            Refresh
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Total Agents"
              value={agents.length}
              icon={<InfoIcon color="primary" />}
              tooltip="Total number of configured agents"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Active Agents"
              value={agents.filter((a) => a.status === 'active').length}
              icon={<CheckCircleIcon color="success" />}
              tooltip="Number of currently active agents"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Warning"
              value={agents.filter((a) => a.status === 'warning').length}
              icon={<WarningIcon color="warning" />}
              tooltip="Number of agents with warnings"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Errors"
              value={agents.filter((a) => a.status === 'error').length}
              icon={<ErrorIcon color="error" />}
              tooltip="Number of agents with errors"
            />
          </Grid>
        </Grid>

        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Agent Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>CPU Usage</TableCell>
                <TableCell>Memory Usage</TableCell>
                <TableCell>Tasks</TableCell>
                <TableCell>Last Updated</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {agents.map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell>{agent.name}</TableCell>
                  <TableCell>
                    <Chip
                      icon={getStatusIcon(agent.status)}
                      label={agent.status}
                      color={getStatusColor(agent.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={agent.cpuUsage}
                          color={agent.cpuUsage > 80 ? 'error' : 'primary'}
                        />
                      </Box>
                      <Typography variant="body2">{agent.cpuUsage}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={agent.memoryUsage}
                          color={agent.memoryUsage > 80 ? 'error' : 'primary'}
                        />
                      </Box>
                      <Typography variant="body2">{agent.memoryUsage}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {agent.activeTasks} / {agent.maxTasks}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {new Date(agent.lastUpdated).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      onClick={() => handleViewDetails(agent)}
                    >
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Dialog
          open={isDetailsOpen}
          onClose={handleCloseDetails}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Agent Details</DialogTitle>
          <DialogContent>
            {selectedAgent && (
              <Box mt={2}>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Typography variant="h6">{selectedAgent.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedAgent.description}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1">Performance Metrics</Typography>
                    <Box mt={2}>
                      <Typography variant="body2">CPU Usage: {selectedAgent.cpuUsage}%</Typography>
                      <Typography variant="body2">Memory Usage: {selectedAgent.memoryUsage}%</Typography>
                      <Typography variant="body2">Active Tasks: {selectedAgent.activeTasks}</Typography>
                      <Typography variant="body2">Response Time: {selectedAgent.responseTime}ms</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1">Recent Activity</Typography>
                    <Box mt={2}>
                      {selectedAgent.recentActivity?.map((activity, index) => (
                        <Box key={index} mb={1}>
                          <Typography variant="body2">
                            {new Date(activity.timestamp).toLocaleString()}: {activity.description}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDetails}>Close</Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </motion.div>
  );
};

export default AgentMonitor;

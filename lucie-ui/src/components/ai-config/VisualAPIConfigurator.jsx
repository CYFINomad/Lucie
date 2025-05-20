import React from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Switch,
  FormControlLabel,
  Slider,
  Grid,
  Divider,
  Alert,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';

const VisualAPIConfigurator = ({ apiConfig, onConfigUpdate }) => {
  const { theme } = useTheme();

  const handleConfigChange = (field, value) => {
    onConfigUpdate({
      ...apiConfig,
      [field]: value,
    });
  };

  return (
    <Box sx={{ p: 2 }}>
      <Paper
        elevation={0}
        sx={{
          p: 3,
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Typography variant="h6" gutterBottom>
          API Configuration
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="API Endpoint"
              value={apiConfig.endpoint}
              onChange={(e) => handleConfigChange('endpoint', e.target.value)}
              margin="normal"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="API Version"
              value={apiConfig.version}
              onChange={(e) => handleConfigChange('version', e.target.value)}
              margin="normal"
            />
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={apiConfig.ssl}
                  onChange={(e) => handleConfigChange('ssl', e.target.checked)}
                  color="primary"
                />
              }
              label="Enable SSL"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography gutterBottom>Request Timeout (seconds)</Typography>
            <Slider
              value={apiConfig.timeout}
              onChange={(_, value) => handleConfigChange('timeout', value)}
              min={1}
              max={60}
              step={1}
              valueLabelDisplay="auto"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography gutterBottom>Rate Limiting (requests per minute)</Typography>
            <Slider
              value={apiConfig.rateLimit}
              onChange={(_, value) => handleConfigChange('rateLimit', value)}
              min={1}
              max={100}
              step={1}
              valueLabelDisplay="auto"
            />
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={apiConfig.retryOnFailure}
                  onChange={(e) => handleConfigChange('retryOnFailure', e.target.checked)}
                  color="primary"
                />
              }
              label="Retry on Failure"
            />
          </Grid>

          {apiConfig.retryOnFailure && (
            <Grid item xs={12}>
              <Typography gutterBottom>Max Retries</Typography>
              <Slider
                value={apiConfig.maxRetries}
                onChange={(_, value) => handleConfigChange('maxRetries', value)}
                min={1}
                max={5}
                step={1}
                valueLabelDisplay="auto"
              />
            </Grid>
          )}

          <Grid item xs={12}>
            <Alert severity="info" sx={{ mt: 2 }}>
              Changes to API configuration will take effect after saving and restarting the service.
            </Alert>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default VisualAPIConfigurator;

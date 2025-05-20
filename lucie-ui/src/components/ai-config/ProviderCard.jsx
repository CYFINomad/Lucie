import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  IconButton,
  Grid,
  Chip,
  Tooltip,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import SecurityIcon from '@mui/icons-material/Security';

const ProviderCard = ({ providers, onProviderUpdate }) => {
  const { theme } = useTheme();

  const handleAddProvider = () => {
    const newProvider = {
      id: Date.now().toString(),
      name: '',
      apiKey: '',
      baseUrl: '',
      status: 'inactive',
    };
    onProviderUpdate([...providers, newProvider]);
  };

  const handleDeleteProvider = (providerId) => {
    onProviderUpdate(providers.filter(p => p.id !== providerId));
  };

  const handleProviderChange = (providerId, field, value) => {
    const updatedProviders = providers.map(provider =>
      provider.id === providerId
        ? { ...provider, [field]: value }
        : provider
    );
    onProviderUpdate(updatedProviders);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">AI Service Providers</Typography>
        <Tooltip title="Add Provider">
          <IconButton
            onClick={handleAddProvider}
            color="primary"
            sx={{ backgroundColor: theme.palette.primary.light }}
          >
            <AddIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Grid container spacing={3}>
        {providers.map((provider) => (
          <Grid item xs={12} md={6} key={provider.id}>
            <Card
              sx={{
                height: '100%',
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
              }}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <TextField
                    fullWidth
                    label="Provider Name"
                    value={provider.name}
                    onChange={(e) => handleProviderChange(provider.id, 'name', e.target.value)}
                    margin="normal"
                  />
                  <IconButton
                    onClick={() => handleDeleteProvider(provider.id)}
                    color="error"
                    sx={{ ml: 1 }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>

                <TextField
                  fullWidth
                  label="API Key"
                  type="password"
                  value={provider.apiKey}
                  onChange={(e) => handleProviderChange(provider.id, 'apiKey', e.target.value)}
                  margin="normal"
                  InputProps={{
                    endAdornment: (
                      <SecurityIcon color="action" sx={{ mr: 1 }} />
                    ),
                  }}
                />

                <TextField
                  fullWidth
                  label="Base URL"
                  value={provider.baseUrl}
                  onChange={(e) => handleProviderChange(provider.id, 'baseUrl', e.target.value)}
                  margin="normal"
                />

                <Box mt={2} display="flex" alignItems="center">
                  <Chip
                    label={provider.status}
                    color={provider.status === 'active' ? 'success' : 'default'}
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {provider.status === 'active' ? 'Connected' : 'Not connected'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ProviderCard;

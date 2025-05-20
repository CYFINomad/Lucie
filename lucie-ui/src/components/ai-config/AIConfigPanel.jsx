import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Divider,
  useTheme,
} from '@mui/material';
import ModelSelector from './ModelSelector';
import ProviderCard from './ProviderCard';
import VisualAPIConfigurator from './VisualAPIConfigurator';
import { useAIConfig } from '../../hooks/useAIConfig';

const AIConfigPanel = () => {
  const [activeTab, setActiveTab] = useState(0);
  const { theme } = useTheme();
  const { config, updateConfig, saveConfig } = useAIConfig();

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleConfigUpdate = (updates) => {
    updateConfig(updates);
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 3,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: theme.palette.background.paper,
      }}
    >
      <Typography variant="h5" gutterBottom>
        AI Configuration
      </Typography>
      <Divider sx={{ mb: 3 }} />

      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        sx={{ borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="Models" />
        <Tab label="Providers" />
        <Tab label="API Settings" />
      </Tabs>

      <Box sx={{ mt: 3, flex: 1, overflow: 'auto' }}>
        {activeTab === 0 && (
          <ModelSelector
            selectedModels={config.models}
            onModelChange={(models) => handleConfigUpdate({ models })}
          />
        )}
        {activeTab === 1 && (
          <ProviderCard
            providers={config.providers}
            onProviderUpdate={(providers) => handleConfigUpdate({ providers })}
          />
        )}
        {activeTab === 2 && (
          <VisualAPIConfigurator
            apiConfig={config.api}
            onConfigUpdate={(api) => handleConfigUpdate({ api })}
          />
        )}
      </Box>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <button
          onClick={saveConfig}
          className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
        >
          Save Configuration
        </button>
      </Box>
    </Paper>
  );
};

export default AIConfigPanel;

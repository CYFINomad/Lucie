import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Slider,
  TextField,
  Grid,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';

const ModelSelector = ({ selectedModels, onModelChange }) => {
  const { theme } = useTheme();

  const handleModelToggle = (modelId) => {
    const updatedModels = selectedModels.map(model =>
      model.id === modelId
        ? { ...model, enabled: !model.enabled }
        : model
    );
    onModelChange(updatedModels);
  };

  const handleParameterChange = (modelId, paramName, value) => {
    const updatedModels = selectedModels.map(model =>
      model.id === modelId
        ? {
            ...model,
            parameters: {
              ...model.parameters,
              [paramName]: value,
            },
          }
        : model
    );
    onModelChange(updatedModels);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Grid container spacing={3}>
        {selectedModels.map((model) => (
          <Grid item xs={12} md={6} key={model.id}>
            <Card
              sx={{
                height: '100%',
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
              }}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">{model.name}</Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={model.enabled}
                        onChange={() => handleModelToggle(model.id)}
                        color="primary"
                      />
                    }
                    label="Enabled"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {model.description}
                </Typography>

                {model.enabled && (
                  <Box mt={2}>
                    {model.parameters && Object.entries(model.parameters).map(([key, value]) => (
                      <Box key={key} mb={2}>
                        <Typography variant="body2" gutterBottom>
                          {key}
                        </Typography>
                        {typeof value === 'number' ? (
                          <Slider
                            value={value}
                            onChange={(_, newValue) =>
                              handleParameterChange(model.id, key, newValue)
                            }
                            min={0}
                            max={1}
                            step={0.1}
                            valueLabelDisplay="auto"
                          />
                        ) : (
                          <TextField
                            fullWidth
                            size="small"
                            value={value}
                            onChange={(e) =>
                              handleParameterChange(model.id, key, e.target.value)
                            }
                          />
                        )}
                      </Box>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ModelSelector;

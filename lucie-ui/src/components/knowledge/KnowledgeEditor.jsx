import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  Grid,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import { motion } from 'framer-motion';

const KnowledgeEditor = ({ knowledge, onSave, onDelete, availableConcepts }) => {
  const { theme } = useTheme();
  const [editedKnowledge, setEditedKnowledge] = useState(knowledge);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedConcept, setSelectedConcept] = useState(null);

  const handleChange = (field, value) => {
    setEditedKnowledge(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleAddRelationship = () => {
    setIsDialogOpen(true);
  };

  const handleSaveRelationship = () => {
    if (selectedConcept) {
      setEditedKnowledge(prev => ({
        ...prev,
        relationships: [
          ...prev.relationships,
          {
            targetId: selectedConcept.id,
            type: 'related',
            strength: 0.5,
          },
        ],
      }));
    }
    setIsDialogOpen(false);
    setSelectedConcept(null);
  };

  const handleDeleteRelationship = (targetId) => {
    setEditedKnowledge(prev => ({
      ...prev,
      relationships: prev.relationships.filter(rel => rel.targetId !== targetId),
    }));
  };

  const handleSave = () => {
    onSave(editedKnowledge);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
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
          <Typography variant="h6">Knowledge Editor</Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSave}
            startIcon={<EditIcon />}
          >
            Save Changes
          </Button>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Title"
              value={editedKnowledge.title}
              onChange={(e) => handleChange('title', e.target.value)}
              margin="normal"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Description"
              value={editedKnowledge.description}
              onChange={(e) => handleChange('description', e.target.value)}
              margin="normal"
              multiline
              rows={4}
            />
          </Grid>

          <Grid item xs={12}>
            <Box display="flex" alignItems="center" mb={2}>
              <Typography variant="subtitle1" sx={{ mr: 2 }}>
                Relationships
              </Typography>
              <IconButton
                color="primary"
                onClick={handleAddRelationship}
                sx={{ backgroundColor: theme.palette.primary.light }}
              >
                <AddIcon />
              </IconButton>
            </Box>

            <Box display="flex" flexWrap="wrap" gap={1}>
              {editedKnowledge.relationships.map((rel) => {
                const targetConcept = availableConcepts.find(c => c.id === rel.targetId);
                return (
                  <Chip
                    key={rel.targetId}
                    label={targetConcept?.name || 'Unknown'}
                    onDelete={() => handleDeleteRelationship(rel.targetId)}
                    color="primary"
                    variant="outlined"
                  />
                );
              })}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Box display="flex" justifyContent="flex-end">
              <Button
                variant="outlined"
                color="error"
                onClick={() => onDelete(editedKnowledge.id)}
                startIcon={<DeleteIcon />}
              >
                Delete
              </Button>
            </Box>
          </Grid>
        </Grid>

        <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)}>
          <DialogTitle>Add Relationship</DialogTitle>
          <DialogContent>
            <Autocomplete
              options={availableConcepts}
              getOptionLabel={(option) => option.name}
              value={selectedConcept}
              onChange={(_, newValue) => setSelectedConcept(newValue)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Select Concept"
                  margin="normal"
                  fullWidth
                />
              )}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setIsDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSaveRelationship} color="primary">
              Add
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </motion.div>
  );
};

export default KnowledgeEditor;

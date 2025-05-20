import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Rating,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Chip,
  Stack,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import { motion } from 'framer-motion';
import SentimentVeryDissatisfiedIcon from '@mui/icons-material/SentimentVeryDissatisfied';
import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';
import SentimentSatisfiedIcon from '@mui/icons-material/SentimentSatisfied';
import SentimentSatisfiedAltIcon from '@mui/icons-material/SentimentSatisfiedAlt';
import SentimentVerySatisfiedIcon from '@mui/icons-material/SentimentVerySatisfied';

const customIcons = {
  1: { icon: <SentimentVeryDissatisfiedIcon />, label: 'Very Dissatisfied' },
  2: { icon: <SentimentDissatisfiedIcon />, label: 'Dissatisfied' },
  3: { icon: <SentimentSatisfiedIcon />, label: 'Neutral' },
  4: { icon: <SentimentSatisfiedAltIcon />, label: 'Satisfied' },
  5: { icon: <SentimentVerySatisfiedIcon />, label: 'Very Satisfied' },
};

const FeedbackForm = ({ onSubmit, initialData = {} }) => {
  const { theme } = useTheme();
  const [feedback, setFeedback] = useState({
    rating: initialData.rating || 0,
    accuracy: initialData.accuracy || 'neutral',
    helpfulness: initialData.helpfulness || 'neutral',
    comments: initialData.comments || '',
    tags: initialData.tags || [],
  });

  const [newTag, setNewTag] = useState('');

  const handleChange = (field, value) => {
    setFeedback(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleAddTag = () => {
    if (newTag && !feedback.tags.includes(newTag)) {
      setFeedback(prev => ({
        ...prev,
        tags: [...prev.tags, newTag],
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFeedback(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove),
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(feedback);
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
        <Typography variant="h6" gutterBottom>
          Feedback Form
        </Typography>

        <form onSubmit={handleSubmit}>
          <Box mb={3}>
            <Typography component="legend">Overall Rating</Typography>
            <Rating
              name="rating"
              value={feedback.rating}
              onChange={(_, value) => handleChange('rating', value)}
              max={5}
              sx={{ mt: 1 }}
            />
          </Box>

          <Box mb={3}>
            <FormControl component="fieldset">
              <FormLabel component="legend">Response Accuracy</FormLabel>
              <RadioGroup
                row
                value={feedback.accuracy}
                onChange={(e) => handleChange('accuracy', e.target.value)}
              >
                <FormControlLabel value="poor" control={<Radio />} label="Poor" />
                <FormControlLabel value="neutral" control={<Radio />} label="Neutral" />
                <FormControlLabel value="good" control={<Radio />} label="Good" />
              </RadioGroup>
            </FormControl>
          </Box>

          <Box mb={3}>
            <FormControl component="fieldset">
              <FormLabel component="legend">Helpfulness</FormLabel>
              <RadioGroup
                row
                value={feedback.helpfulness}
                onChange={(e) => handleChange('helpfulness', e.target.value)}
              >
                <FormControlLabel value="poor" control={<Radio />} label="Poor" />
                <FormControlLabel value="neutral" control={<Radio />} label="Neutral" />
                <FormControlLabel value="good" control={<Radio />} label="Good" />
              </RadioGroup>
            </FormControl>
          </Box>

          <Box mb={3}>
            <TextField
              fullWidth
              label="Additional Comments"
              multiline
              rows={4}
              value={feedback.comments}
              onChange={(e) => handleChange('comments', e.target.value)}
            />
          </Box>

          <Box mb={3}>
            <Typography gutterBottom>Tags</Typography>
            <Box display="flex" gap={1} mb={1}>
              <TextField
                size="small"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                placeholder="Add a tag"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
              />
              <Button
                variant="outlined"
                onClick={handleAddTag}
                disabled={!newTag}
              >
                Add
              </Button>
            </Box>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {feedback.tags.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  onDelete={() => handleRemoveTag(tag)}
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Stack>
          </Box>

          <Box display="flex" justifyContent="flex-end">
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={!feedback.rating}
            >
              Submit Feedback
            </Button>
          </Box>
        </form>
      </Paper>
    </motion.div>
  );
};

export default FeedbackForm;

import React from 'react';
import { Paper, Typography, Box } from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import { motion } from 'framer-motion';

const SuggestionBubble = ({ suggestion, onClick, isHighlighted = false }) => {
  const { theme } = useTheme();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Paper
        elevation={isHighlighted ? 3 : 1}
        onClick={() => onClick?.(suggestion)}
        sx={{
          p: 2,
          mb: 1,
          cursor: onClick ? 'pointer' : 'default',
          backgroundColor: isHighlighted 
            ? theme.palette.primary.light 
            : theme.palette.background.paper,
          border: `1px solid ${isHighlighted 
            ? theme.palette.primary.main 
            : theme.palette.divider}`,
          '&:hover': {
            backgroundColor: onClick 
              ? theme.palette.action.hover 
              : theme.palette.background.paper,
            transform: onClick ? 'translateY(-2px)' : 'none',
            transition: 'all 0.2s ease-in-out',
          },
        }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <Typography
            variant="body1"
            color={isHighlighted 
              ? theme.palette.primary.contrastText 
              : theme.palette.text.primary}
          >
            {suggestion.text}
          </Typography>
          {suggestion.icon && (
            <Box component="span" sx={{ ml: 'auto' }}>
              {suggestion.icon}
            </Box>
          )}
        </Box>
        {suggestion.description && (
          <Typography
            variant="caption"
            color={theme.palette.text.secondary}
            sx={{ mt: 1, display: 'block' }}
          >
            {suggestion.description}
          </Typography>
        )}
      </Paper>
    </motion.div>
  );
};

export default SuggestionBubble;

import React, { useEffect, useState } from 'react';
import { Box, Typography, LinearProgress, useTheme } from '@mui/material';

/**
 * Affichage visuel pendant la génération de réponse
 * Inclut une animation "style Jarvis" basique
 */
const ResponseDisplay = () => {
  const theme = useTheme();
  const [dots, setDots] = useState('.');
  const [progress, setProgress] = useState(0);

  // Animation des points de chargement
  useEffect(() => {
    const dotsInterval = setInterval(() => {
      setDots(prevDots => {
        if (prevDots.length >= 3) return '.';
        return prevDots + '.';
      });
    }, 500);

    return () => clearInterval(dotsInterval);
  }, []);

  // Animation de la barre de progression
  useEffect(() => {
    const progressInterval = setInterval(() => {
      setProgress(prevProgress => {
        // Reset ou incrément avec effet aléatoire
        if (prevProgress >= 100) {
          return 0;
        }
        
        // Progression aléatoire pour simuler un traitement
        return prevProgress + Math.random() * 10;
      });
    }, 300);

    return () => clearInterval(progressInterval);
  }, []);

  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: 100,
        left: '50%',
        transform: 'translateX(-50%)',
        p: 2,
        borderRadius: 2,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        width: { xs: '90%', sm: '60%', md: '40%' },
        maxWidth: 400,
        zIndex: 1000,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
      }}
    >
      <Typography
        variant="body2"
        color={theme.palette.secondary.main}
        sx={{ mb: 1, fontWeight: 'medium' }}
      >
        Lucie réfléchit{dots}
      </Typography>
      
      <LinearProgress 
        color="secondary" 
        variant="determinate" 
        value={progress}
        sx={{ 
          width: '100%', 
          height: 4,
          borderRadius: 2
        }} 
      />
      
      {/* Effet visuel "style Jarvis" basique */}
      <Box
        sx={{
          position: 'absolute',
          width: '110%',
          height: '110%',
          borderRadius: 3,
          border: `1px solid ${theme.palette.secondary.main}`,
          opacity: 0.5,
          animation: 'pulse 2s infinite'
        }}
      />
      
      {/* Définition de l'animation */}
      <Box
        sx={{
          '@keyframes pulse': {
            '0%': {
              transform: 'scale(1)',
              opacity: 0.5
            },
            '50%': {
              transform: 'scale(1.05)',
              opacity: 0.7
            },
            '100%': {
              transform: 'scale(1)',
              opacity: 0.5
            }
          }
        }}
      />
    </Box>
  );
};

export default ResponseDisplay;
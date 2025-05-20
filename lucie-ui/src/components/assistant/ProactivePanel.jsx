import React from "react";
import {
  Box,
  Paper,
  Typography,
  Chip,
  useTheme,
  IconButton,
  Tooltip,
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";

/**
 * Panneau de suggestions proactives
 * Affiche des suggestions contextuelles pour l'utilisateur
 */
const ProactivePanel = ({ suggestions = [], onSuggestionClick }) => {
  const theme = useTheme();

  // Pas de rendu si aucune suggestion
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        mx: "auto",
        borderRadius: 3,
        width: { xs: "95%", sm: "90%", md: "85%" },
        maxWidth: 700,
        backgroundColor: "rgba(30, 30, 30, 0.85)",
        backdropFilter: "blur(8px)",
        border: `1px solid ${theme.palette.secondary.dark}`,
        boxShadow: `0 4px 20px 0px ${theme.palette.secondary.dark}40`,
        transform: "translateY(-10px)",
        animation: "float 3s ease-in-out infinite",
      }}
    >
      {/* En-tête */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          mb: 1.5,
          pb: 1,
          borderBottom: `1px solid ${theme.palette.secondary.dark}30`,
        }}
      >
        <LightbulbOutlinedIcon color="secondary" sx={{ mr: 1 }} />
        <Typography
          variant="subtitle1"
          color="secondary"
          sx={{ fontWeight: 500 }}
        >
          Suggestions pour démarrer
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        <Tooltip title="Suggestions basées sur l'analyse contextuelle">
          <IconButton
            size="small"
            color="primary"
            sx={{
              backgroundColor: theme.palette.background.paper,
              "&:hover": {
                backgroundColor: theme.palette.background.default,
              },
            }}
          >
            <AutoAwesomeIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Contenu des suggestions */}
      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          gap: 1,
          justifyContent: "center",
        }}
      >
        {suggestions.map((suggestion, index) => (
          <Chip
            key={index}
            label={suggestion}
            onClick={() => onSuggestionClick(suggestion)}
            color="secondary"
            variant="outlined"
            clickable
            sx={{
              px: 1,
              py: 2.5,
              borderRadius: 2,
              fontSize: "0.9rem",
              borderWidth: 1,
              borderColor: theme.palette.secondary.dark,
              backgroundColor: "rgba(106, 53, 224, 0.1)",
              "&:hover": {
                backgroundColor: "rgba(106, 53, 224, 0.2)",
                boxShadow: `0 0 10px ${theme.palette.secondary.main}80`,
              },
              transition: "all 0.3s ease",
            }}
          />
        ))}
      </Box>

      {/* Styles CSS pour l'animation flottante */}
      <style jsx="true">{`
        @keyframes float {
          0% {
            transform: translateY(-10px);
          }
          50% {
            transform: translateY(-15px);
          }
          100% {
            transform: translateY(-10px);
          }
        }
      `}</style>
    </Paper>
  );
};

export default ProactivePanel;

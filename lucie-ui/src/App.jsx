import React from "react";
import {
  createTheme,
  ThemeProvider,
  CssBaseline,
  Box,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  useMediaQuery,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import SettingsIcon from "@mui/icons-material/Settings";
import ChatInterface from "./components/chat/ChatInterface";

// Thème personnalisé pour Lucie
const createAppTheme = (prefersDarkMode) =>
  createTheme({
    palette: {
      mode: prefersDarkMode ? "dark" : "dark", // Toujours dark mode
      primary: {
        main: "#8c5eff", // Violet pour les éléments principaux
        light: "#b38fff",
        dark: "#6a35e0",
        contrastText: "#ffffff",
      },
      secondary: {
        main: "#6a35e0", // Violet plus foncé comme couleur secondaire
        light: "#8c5eff",
        dark: "#4d1fc0",
        contrastText: "#ffffff",
      },
      background: {
        default: "#121212", // Gris très foncé/noir pour le fond
        paper: "#1e1e1e", // Gris foncé pour les éléments
      },
      text: {
        primary: "#ffffff", // Texte principal en blanc
        secondary: "rgba(255, 255, 255, 0.7)", // Texte secondaire en blanc avec opacité
      },
      error: {
        main: "#ff3d71",
      },
      info: {
        main: "#8c5eff", // Violet pour info
      },
      success: {
        main: "#a988ff", // Violet plus clair pour les succès
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 300,
        color: "#8c5eff", // Titres en violet pour se démarquer
      },
      h6: {
        fontWeight: 400,
        color: "#8c5eff", // Sous-titres en violet
      },
      // Corps de texte en blanc par défaut via text.primary
    },
    shape: {
      borderRadius: 8,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: "none",
            borderRadius: 8,
          },
          contained: {
            boxShadow: "0 0 8px rgba(140, 94, 255, 0.3)",
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
            borderRadius: 12,
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            background: "#1e1e1e",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.5)",
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            background: "#1e1e1e",
            border: "1px solid rgba(140, 94, 255, 0.2)",
            boxShadow: "0 8px 16px rgba(0, 0, 0, 0.5)",
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            backgroundColor: "rgba(140, 94, 255, 0.15)",
          },
        },
      },
      // Pour les messages de chat spécifiquement
      MuiTypography: {
        styleOverrides: {
          root: {
            // Par défaut le texte sera blanc grâce à text.primary
          },
          // Vous pouvez ajouter des styles spécifiques pour les variantes si nécessaire
          body1: {
            // Style pour le texte principal, notamment dans les messages
            color: "#ffffff",
          },
          body2: {
            // Style pour le texte secondaire
            color: "rgba(255, 255, 255, 0.7)",
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            "& label": {
              color: "rgba(255, 255, 255, 0.7)", // Labels en blanc avec opacité
            },
            "& label.Mui-focused": {
              color: "#8c5eff", // Labels en focus en violet
            },
            "& .MuiOutlinedInput-root": {
              "& fieldset": {
                borderColor: "rgba(140, 94, 255, 0.3)",
              },
              "&:hover fieldset": {
                borderColor: "rgba(140, 94, 255, 0.5)",
              },
              "&.Mui-focused fieldset": {
                borderColor: "#8c5eff",
              },
              "& input": {
                color: "#ffffff", // Texte d'entrée en blanc
              },
            },
          },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          switchBase: {
            "&.Mui-checked": {
              color: "#8c5eff",
              "& + .MuiSwitch-track": {
                backgroundColor: "#6a35e0",
              },
            },
          },
          track: {
            backgroundColor: "#333333",
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            backgroundColor: "rgba(140, 94, 255, 0.15)",
          },
          bar: {
            backgroundColor: "#8c5eff",
          },
        },
      },
    },
  });

function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const theme = React.useMemo(
    () => createAppTheme(prefersDarkMode),
    [prefersDarkMode]
  );

  // État pour gérer l'affichage du panneau de configuration (non implémenté)
  const [showSettings, setShowSettings] = React.useState(false);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: "flex", flexDirection: "column", height: "100vh" }}>
        {/* Barre d'applications */}
        <AppBar position="static" color="transparent" elevation={0}>
          <Toolbar>
            <IconButton
              size="large"
              edge="start"
              color="inherit"
              aria-label="menu"
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography
              variant="h6"
              component="div"
              sx={{ flexGrow: 1, color: theme.palette.secondary.main }}
            >
              Lucie
              <Typography
                component="span"
                variant="caption"
                sx={{ ml: 1, opacity: 0.7 }}
              >
                v0.1.0 Alpha
              </Typography>
            </Typography>
            <IconButton
              color="inherit"
              aria-label="settings"
              onClick={() => setShowSettings(!showSettings)}
            >
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Conteneur principal */}
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", md: "row" },
            flexGrow: 1,
            overflow: "hidden",
          }}
        >
          {/* Zone de chat (contenu principal) */}
          <Box
            sx={{
              flexGrow: 1,
              display: "flex",
              flexDirection: "column",
              height: { xs: "calc(100vh - 64px)", md: "100%" },
            }}
          >
            <ChatInterface />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;

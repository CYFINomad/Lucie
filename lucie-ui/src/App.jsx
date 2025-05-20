import React, { useState, useEffect } from "react";
import {
  createTheme,
  ThemeProvider,
  CssBaseline,
  Box,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  useMediaQuery,
  Fade,
  Tooltip,
  CircularProgress,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import SettingsIcon from "@mui/icons-material/Settings";
import ChatIcon from "@mui/icons-material/Chat";
import HistoryIcon from "@mui/icons-material/History";
import ScienceIcon from "@mui/icons-material/Science";
import InfoIcon from "@mui/icons-material/Info";
import CloseIcon from "@mui/icons-material/Close";
import EnhancedChatInterface from "./components/chat/EnhancedChatInterface";
import apiClient from "./services/apiClient";
import chatService from "./services/chatService";

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
        main: "#00d4ff", // Bleu cyan pour info
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
      // Styles pour le drawer
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: "#1a1a1a",
            borderRight: "1px solid rgba(140, 94, 255, 0.1)",
          },
        },
      },
      // Styles pour les listes
      MuiListItem: {
        styleOverrides: {
          root: {
            "&.Mui-selected": {
              backgroundColor: "rgba(140, 94, 255, 0.2)",
              "&:hover": {
                backgroundColor: "rgba(140, 94, 255, 0.25)",
              },
              "&::before": {
                content: '""',
                position: "absolute",
                left: 0,
                top: "10%",
                height: "80%",
                width: 3,
                backgroundColor: "#8c5eff",
                borderRadius: "0 4px 4px 0",
              },
            },
            "&:hover": {
              backgroundColor: "rgba(255, 255, 255, 0.05)",
            },
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
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  // État pour le drawer (menu latéral)
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedMenuItem, setSelectedMenuItem] = useState("chat");
  const [isLoading, setIsLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState({
    available: false,
    message: "Vérification de la connexion...",
  });

  // Vérifier l'état du backend au chargement
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        setIsLoading(true);
        const status = await apiClient.checkHealth();
        setBackendStatus({
          available: true,
          message: "Connecté au backend",
          details: status,
        });

        // Initialiser le service de chat
        await chatService.startNewConversation();
      } catch (error) {
        setBackendStatus({
          available: false,
          message: "Impossible de se connecter au backend",
          error: error.message,
        });
        console.error("Backend connection error:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkBackendStatus();
  }, []);

  // Gérer la fermeture du drawer
  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  // Gérer la navigation
  const handleNavigation = (menuItem) => {
    setSelectedMenuItem(menuItem);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  // Contenu du drawer
  const drawerContent = (
    <Box sx={{ width: 250 }} role="presentation">
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          p: 2,
        }}
      >
        <Typography variant="h6" color="secondary">
          Lucie AI
        </Typography>
        {isMobile && (
          <IconButton onClick={toggleDrawer}>
            <CloseIcon />
          </IconButton>
        )}
      </Box>
      <Divider sx={{ backgroundColor: "rgba(140, 94, 255, 0.2)" }} />
      <List>
        <ListItem
          button
          selected={selectedMenuItem === "chat"}
          onClick={() => handleNavigation("chat")}
        >
          <ListItemIcon>
            <ChatIcon
              color={selectedMenuItem === "chat" ? "secondary" : "inherit"}
            />
          </ListItemIcon>
          <ListItemText primary="Conversation" />
        </ListItem>
        <ListItem
          button
          selected={selectedMenuItem === "history"}
          onClick={() => handleNavigation("history")}
        >
          <ListItemIcon>
            <HistoryIcon
              color={selectedMenuItem === "history" ? "secondary" : "inherit"}
            />
          </ListItemIcon>
          <ListItemText primary="Historique" />
        </ListItem>
        <ListItem
          button
          selected={selectedMenuItem === "agents"}
          onClick={() => handleNavigation("agents")}
        >
          <ListItemIcon>
            <ScienceIcon
              color={selectedMenuItem === "agents" ? "secondary" : "inherit"}
            />
          </ListItemIcon>
          <ListItemText primary="Agents" />
        </ListItem>
      </List>
      <Divider sx={{ backgroundColor: "rgba(140, 94, 255, 0.2)" }} />
      <List>
        <ListItem
          button
          selected={selectedMenuItem === "settings"}
          onClick={() => handleNavigation("settings")}
        >
          <ListItemIcon>
            <SettingsIcon
              color={selectedMenuItem === "settings" ? "secondary" : "inherit"}
            />
          </ListItemIcon>
          <ListItemText primary="Paramètres" />
        </ListItem>
        <ListItem
          button
          selected={selectedMenuItem === "about"}
          onClick={() => handleNavigation("about")}
        >
          <ListItemIcon>
            <InfoIcon
              color={selectedMenuItem === "about" ? "secondary" : "inherit"}
            />
          </ListItemIcon>
          <ListItemText primary="À propos" />
        </ListItem>
      </List>
      <Box sx={{ p: 2, mt: 2 }}>
        <Typography variant="caption" color="text.secondary">
          Version 0.1.0 Alpha
        </Typography>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            mt: 1,
          }}
        >
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: backendStatus.available
                ? theme.palette.success.main
                : theme.palette.error.main,
              mr: 1,
            }}
          />
          <Typography variant="caption" color="text.secondary">
            {backendStatus.message}
          </Typography>
        </Box>
      </Box>
    </Box>
  );

  // Page de chargement
  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            height: "100vh",
            width: "100vw",
            backgroundColor: theme.palette.background.default,
          }}
        >
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              p: 4,
              borderRadius: 2,
              backgroundColor: "rgba(140, 94, 255, 0.05)",
              border: "1px solid rgba(140, 94, 255, 0.2)",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.2)",
              maxWidth: 400,
            }}
          >
            <Typography
              variant="h4"
              color="secondary"
              sx={{ mb: 3, fontWeight: 300 }}
            >
              Lucie
            </Typography>
            <CircularProgress
              color="secondary"
              size={50}
              thickness={4}
              sx={{ mb: 3 }}
            />
            <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
              Initialisation en cours...
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {backendStatus.message}
            </Typography>
          </Box>
        </Box>
      </ThemeProvider>
    );
  }

  // Page d'erreur si le backend n'est pas disponible
  if (!backendStatus.available) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            height: "100vh",
            width: "100vw",
            backgroundColor: theme.palette.background.default,
          }}
        >
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              p: 4,
              borderRadius: 2,
              backgroundColor: "rgba(255, 61, 113, 0.05)",
              border: "1px solid rgba(255, 61, 113, 0.2)",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.2)",
              maxWidth: 500,
            }}
          >
            <Typography variant="h4" color="error" sx={{ mb: 3 }}>
              Erreur de connexion
            </Typography>
            <Typography variant="body1" color="text.primary" sx={{ mb: 3 }}>
              Impossible de se connecter au backend de Lucie. Veuillez vérifier
              que le serveur est en cours d'exécution et réessayer.
            </Typography>
            <Typography variant="body2" color="error" sx={{ mb: 3 }}>
              {backendStatus.error}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Si le problème persiste, consultez la documentation ou contactez
              le support.
            </Typography>
          </Box>
        </Box>
      </ThemeProvider>
    );
  }

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
              onClick={toggleDrawer}
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
            <Tooltip title="Paramètres">
              <IconButton
                color="inherit"
                aria-label="settings"
                onClick={() => handleNavigation("settings")}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Toolbar>
        </AppBar>

        {/* Contenu principal avec drawer */}
        <Box sx={{ display: "flex", flexGrow: 1, overflow: "hidden" }}>
          {/* Drawer (menu latéral) */}
          <Drawer
            variant={isMobile ? "temporary" : "permanent"}
            open={isMobile ? drawerOpen : true}
            onClose={toggleDrawer}
            sx={{
              width: 250,
              flexShrink: 0,
              "& .MuiDrawer-paper": {
                width: 250,
                boxSizing: "border-box",
              },
            }}
          >
            {drawerContent}
          </Drawer>

          {/* Zone de contenu principal */}
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              overflow: "auto",
              p: { xs: 1, sm: 2 },
              display: "flex",
              flexDirection: "column",
            }}
          >
            {/* Interface de conversation */}
            <Fade in={selectedMenuItem === "chat"}>
              <Box
                sx={{
                  display: selectedMenuItem === "chat" ? "flex" : "none",
                  flexDirection: "column",
                  height: "100%",
                  width: "100%",
                }}
              >
                <EnhancedChatInterface />
              </Box>
            </Fade>

            {/* Historique des conversations (à implémenter) */}
            <Fade in={selectedMenuItem === "history"}>
              <Box
                sx={{
                  display: selectedMenuItem === "history" ? "flex" : "none",
                  flexDirection: "column",
                  height: "100%",
                  width: "100%",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <Box
                  sx={{
                    p: 4,
                    borderRadius: 2,
                    backgroundColor: "rgba(140, 94, 255, 0.05)",
                    border: "1px solid rgba(140, 94, 255, 0.2)",
                    textAlign: "center",
                    maxWidth: 500,
                  }}
                >
                  <Typography variant="h6" color="secondary" gutterBottom>
                    Historique des conversations
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Cette fonctionnalité sera disponible dans une prochaine
                    version.
                  </Typography>
                </Box>
              </Box>
            </Fade>

            {/* Agents (à implémenter) */}
            <Fade in={selectedMenuItem === "agents"}>
              <Box
                sx={{
                  display: selectedMenuItem === "agents" ? "flex" : "none",
                  flexDirection: "column",
                  height: "100%",
                  width: "100%",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <Box
                  sx={{
                    p: 4,
                    borderRadius: 2,
                    backgroundColor: "rgba(140, 94, 255, 0.05)",
                    border: "1px solid rgba(140, 94, 255, 0.2)",
                    textAlign: "center",
                    maxWidth: 500,
                  }}
                >
                  <Typography variant="h6" color="secondary" gutterBottom>
                    Agents et extensions
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Le système d'agents sera implémenté dans une version future.
                    Cette fonctionnalité vous permettra d'étendre les capacités
                    de Lucie avec des agents spécialisés.
                  </Typography>
                </Box>
              </Box>
            </Fade>

            {/* Paramètres (à implémenter) */}
            <Fade in={selectedMenuItem === "settings"}>
              <Box
                sx={{
                  display: selectedMenuItem === "settings" ? "flex" : "none",
                  flexDirection: "column",
                  height: "100%",
                  width: "100%",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <Box
                  sx={{
                    p: 4,
                    borderRadius: 2,
                    backgroundColor: "rgba(140, 94, 255, 0.05)",
                    border: "1px solid rgba(140, 94, 255, 0.2)",
                    textAlign: "center",
                    maxWidth: 500,
                  }}
                >
                  <Typography variant="h6" color="secondary" gutterBottom>
                    Paramètres
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Les paramètres de configuration seront disponibles dans une
                    prochaine version.
                  </Typography>
                </Box>
              </Box>
            </Fade>

            {/* À propos (à implémenter) */}
            <Fade in={selectedMenuItem === "about"}>
              <Box
                sx={{
                  display: selectedMenuItem === "about" ? "flex" : "none",
                  flexDirection: "column",
                  height: "100%",
                  width: "100%",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <Box
                  sx={{
                    p: 4,
                    borderRadius: 2,
                    backgroundColor: "rgba(140, 94, 255, 0.05)",
                    border: "1px solid rgba(140, 94, 255, 0.2)",
                    textAlign: "center",
                    maxWidth: 600,
                  }}
                >
                  <Typography variant="h6" color="secondary" gutterBottom>
                    À propos de Lucie
                  </Typography>
                  <Typography variant="body1" paragraph>
                    Lucie est un assistant IA personnel avancé, inspiré du style
                    Jarvis d'Iron Man, conçu pour être une extension de votre
                    cerveau.
                  </Typography>
                  <Typography variant="body1" paragraph>
                    Avec une architecture hybride utilisant Python pour les
                    capacités d'IA avancées et Node.js/React pour l'interface
                    utilisateur, Lucie vise à offrir une expérience utilisateur
                    fluide et intuitive.
                  </Typography>
                  <Typography variant="body1" paragraph>
                    Cette version alpha (v0.1.0) inclut les fonctionnalités de
                    base de conversation. Les fonctionnalités plus avancées
                    comme les agents spécialisés, l'apprentissage continu et
                    l'intégration multi-IA seront ajoutées dans les prochaines
                    versions.
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: "block", mt: 3 }}
                  >
                    © 2025 - Lucie AI - Version 0.1.0 Alpha
                  </Typography>
                </Box>
              </Box>
            </Fade>
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;

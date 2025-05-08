import React from 'react';
import { 
  createTheme, 
  ThemeProvider, 
  CssBaseline, 
  Box, 
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  useMediaQuery
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SettingsIcon from '@mui/icons-material/Settings';
import ChatInterface from './components/chat/ChatInterface';

// Thème personnalisé pour Lucie
const createAppTheme = (prefersDarkMode) => createTheme({
  palette: {
    mode: prefersDarkMode ? 'dark' : 'dark', // Toujours dark mode pour l'instant
    primary: {
      main: '#f8e7b5', // Or pâle
      light: '#fffbd5',
      dark: '#d6c090',
      contrastText: '#000',
    },
    secondary: {
      main: '#36e7fc', // Bleu "Jarvis-like"
      light: '#69ffff',
      dark: '#00b4c9',
      contrastText: '#000',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 300,
    },
    h6: {
      fontWeight: 400,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

function App() {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const theme = React.useMemo(() => createAppTheme(prefersDarkMode), [prefersDarkMode]);
  
  // État pour gérer l'affichage du panneau de configuration (non implémenté)
  const [showSettings, setShowSettings] = React.useState(false);
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
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
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: theme.palette.secondary.main }}>
              Lucie
              <Typography component="span" variant="caption" sx={{ ml: 1, opacity: 0.7 }}>
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
        <Box sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', md: 'row' },
          flexGrow: 1, 
          overflow: 'hidden' 
        }}>
          {/* Zone de chat (contenu principal) */}
          <Box sx={{ 
            flexGrow: 1, 
            display: 'flex',
            flexDirection: 'column',
            height: { xs: 'calc(100vh - 64px)', md: '100%' }
          }}>
            <ChatInterface />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
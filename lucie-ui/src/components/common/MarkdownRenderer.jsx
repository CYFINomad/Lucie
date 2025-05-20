import React from "react";
import ReactMarkdown from "react-markdown";
import {
  Box,
  Typography,
  useTheme,
  Paper,
  Divider,
  Link,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import CircleIcon from "@mui/icons-material/Circle";

/**
 * Rendu de contenu en markdown avec syntaxe colorée pour le code
 * @param {Object} props - Propriétés du composant
 * @param {string} props.content - Contenu markdown à rendre
 */
const MarkdownRenderer = ({ content }) => {
  const theme = useTheme();

  // Composants personnalisés pour le rendu markdown
  const components = {
    // Titres
    h1: ({ node, ...props }) => (
      <Typography
        variant="h5"
        color="secondary"
        gutterBottom
        sx={{ mt: 2, mb: 1, fontWeight: 600 }}
        {...props}
      />
    ),
    h2: ({ node, ...props }) => (
      <Typography
        variant="h6"
        color="secondary"
        gutterBottom
        sx={{ mt: 2, mb: 1, fontWeight: 600 }}
        {...props}
      />
    ),
    h3: ({ node, ...props }) => (
      <Typography
        variant="subtitle1"
        gutterBottom
        sx={{
          mt: 1.5,
          mb: 0.5,
          fontWeight: 600,
          color: theme.palette.secondary.light,
        }}
        {...props}
      />
    ),
    h4: ({ node, ...props }) => (
      <Typography
        variant="subtitle2"
        gutterBottom
        sx={{
          mt: 1.5,
          mb: 0.5,
          fontWeight: 600,
          color: theme.palette.secondary.light,
        }}
        {...props}
      />
    ),

    // Paragraphes et texte
    p: ({ node, ...props }) => (
      <Typography variant="body1" paragraph {...props} />
    ),
    strong: ({ node, ...props }) => (
      <Typography
        component="span"
        sx={{ fontWeight: "bold", color: theme.palette.secondary.light }}
        {...props}
      />
    ),
    em: ({ node, ...props }) => (
      <Typography component="span" sx={{ fontStyle: "italic" }} {...props} />
    ),

    // Listes
    ul: ({ node, ...props }) => <List dense disablePadding {...props} />,
    ol: ({ node, ordered, ...props }) => (
      <List
        dense
        disablePadding
        sx={{ listStyleType: "decimal", pl: 2 }}
        {...props}
      />
    ),
    li: ({ node, ordered, ...props }) => {
      const { children, ...rest } = props;

      return (
        <ListItem
          dense
          disableGutters
          disablePadding
          sx={{
            display: "flex",
            alignItems: "flex-start",
            py: 0.5,
            pl: 1,
          }}
          {...rest}
        >
          {!ordered && (
            <ListItemIcon sx={{ minWidth: 24, mt: 0.5 }}>
              <CircleIcon
                sx={{ fontSize: 6, color: theme.palette.secondary.main }}
              />
            </ListItemIcon>
          )}
          <ListItemText primary={children} sx={{ m: 0 }} />
        </ListItem>
      );
    },

    // Liens
    a: ({ node, ...props }) => (
      <Link
        color="secondary"
        sx={{
          textDecoration: "none",
          "&:hover": {
            textDecoration: "underline",
          },
        }}
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      />
    ),

    // Divider
    hr: ({ node, ...props }) => <Divider sx={{ my: 2 }} />,

    // Images
    img: ({ node, ...props }) => (
      <Box
        component="img"
        sx={{
          maxWidth: "100%",
          height: "auto",
          borderRadius: 1,
          my: 1,
        }}
        {...props}
      />
    ),

    // Code
    code: ({ node, inline, className, children, ...props }) => {
      const match = /language-(\w+)/.exec(className || "");
      const language = match ? match[1] : "javascript";

      return !inline ? (
        <Box sx={{ my: 2, borderRadius: 1, overflow: "hidden" }}>
          <SyntaxHighlighter
            style={atomDark}
            language={language}
            customStyle={{
              margin: 0,
              borderRadius: theme.shape.borderRadius,
              fontSize: "0.85rem",
            }}
            {...props}
          >
            {String(children).replace(/\r?\n$/, "")}
          </SyntaxHighlighter>
        </Box>
      ) : (
        <Typography
          component="code"
          sx={{
            px: 0.5,
            py: 0.25,
            borderRadius: 0.5,
            backgroundColor: "rgba(0, 0, 0, 0.1)",
            fontFamily: "monospace",
            fontSize: "0.9em",
          }}
          {...props}
        >
          {children}
        </Typography>
      );
    },

    // Blockquote
    blockquote: ({ node, ...props }) => (
      <Paper
        elevation={0}
        sx={{
          pl: 2,
          py: 0.5,
          my: 1,
          borderLeft: `4px solid ${theme.palette.secondary.main}50`,
          backgroundColor: "rgba(140, 94, 255, 0.05)",
          borderRadius: 1,
        }}
        {...props}
      />
    ),

    // Tables
    table: ({ node, ...props }) => (
      <Box
        sx={{
          width: "100%",
          overflowX: "auto",
          my: 2,
        }}
      >
        <Box
          component="table"
          sx={{
            width: "100%",
            borderCollapse: "collapse",
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 1,
            overflow: "hidden",
          }}
          {...props}
        />
      </Box>
    ),

    thead: ({ node, ...props }) => (
      <Box
        component="thead"
        sx={{
          backgroundColor: "rgba(140, 94, 255, 0.1)",
        }}
        {...props}
      />
    ),

    tr: ({ node, ...props }) => (
      <Box
        component="tr"
        sx={{
          borderBottom: `1px solid ${theme.palette.divider}`,
          "&:last-child": {
            borderBottom: "none",
          },
        }}
        {...props}
      />
    ),

    th: ({ node, ...props }) => (
      <Box
        component="th"
        sx={{
          py: 1.5,
          px: 2,
          textAlign: "left",
          fontWeight: 600,
          color: theme.palette.secondary.light,
        }}
        {...props}
      />
    ),

    td: ({ node, ...props }) => (
      <Box
        component="td"
        sx={{
          py: 1.5,
          px: 2,
          borderRight: `1px solid ${theme.palette.divider}`,
          "&:last-child": {
            borderRight: "none",
          },
        }}
        {...props}
      />
    ),
  };

  return (
    <Box sx={{ width: "100%" }}>
      <ReactMarkdown components={components}>{content}</ReactMarkdown>
    </Box>
  );
};

export default MarkdownRenderer;

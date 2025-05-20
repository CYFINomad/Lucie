import React, { useEffect, useRef } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import ForceGraph2D from 'force-graph';
import { motion } from 'framer-motion';

const ConceptMap = ({ concepts, onConceptClick, onLinkClick }) => {
  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const { theme } = useTheme();

  useEffect(() => {
    if (!containerRef.current) return;

    const graph = ForceGraph2D()(containerRef.current)
      .graphData({
        nodes: concepts.map(concept => ({
          id: concept.id,
          name: concept.name,
          type: concept.type,
          value: concept.importance,
        })),
        links: concepts.flatMap(concept =>
          concept.relationships.map(rel => ({
            source: concept.id,
            target: rel.targetId,
            type: rel.type,
            strength: rel.strength,
          }))
        ),
      })
      .nodeLabel('name')
      .nodeColor(node => {
        switch (node.type) {
          case 'concept':
            return theme.palette.primary.main;
          case 'entity':
            return theme.palette.secondary.main;
          default:
            return theme.palette.grey[500];
        }
      })
      .nodeRelSize(6)
      .linkColor(link => {
        const strength = link.strength || 0.5;
        return `rgba(${theme.palette.primary.main}, ${strength})`;
      })
      .linkWidth(link => (link.strength || 0.5) * 2)
      .onNodeClick((node, event) => {
        onConceptClick?.(node);
      })
      .onLinkClick((link, event) => {
        onLinkClick?.(link);
      });

    graphRef.current = graph;

    return () => {
      graph.pauseAnimation();
      graph._destructor();
    };
  }, [concepts, theme, onConceptClick, onLinkClick]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 2,
          height: '600px',
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Typography variant="h6" gutterBottom>
          Concept Map
        </Typography>
        <Box
          ref={containerRef}
          sx={{
            width: '100%',
            height: 'calc(100% - 40px)',
            backgroundColor: theme.palette.background.default,
            borderRadius: 1,
          }}
        />
      </Paper>
    </motion.div>
  );
};

export default ConceptMap;

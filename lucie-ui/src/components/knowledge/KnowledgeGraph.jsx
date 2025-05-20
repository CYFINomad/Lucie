import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Zoom,
  CircularProgress,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import ForceGraph3D from '3d-force-graph';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import { motion } from 'framer-motion';

const KnowledgeGraph = ({ knowledge, onNodeClick, onLinkClick }) => {
  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const { theme } = useTheme();
  const [isLoading, setIsLoading] = useState(true);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    if (!containerRef.current) return;

    setIsLoading(true);

    const graph = ForceGraph3D()(containerRef.current)
      .graphData({
        nodes: knowledge.nodes.map(node => ({
          id: node.id,
          name: node.name,
          type: node.type,
          value: node.importance,
          color: node.color,
        })),
        links: knowledge.links.map(link => ({
          source: link.source,
          target: link.target,
          type: link.type,
          strength: link.strength,
        })),
      })
      .nodeLabel('name')
      .nodeColor(node => node.color || theme.palette.primary.main)
      .nodeRelSize(6)
      .linkColor(link => {
        const strength = link.strength || 0.5;
        return `rgba(${theme.palette.primary.main}, ${strength})`;
      })
      .linkWidth(link => (link.strength || 0.5) * 2)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleSpeed(0.005)
      .onNodeClick((node, event) => {
        onNodeClick?.(node);
      })
      .onLinkClick((link, event) => {
        onLinkClick?.(link);
      })
      .onEngineStop(() => {
        setIsLoading(false);
      });

    graphRef.current = graph;

    return () => {
      graph.pauseAnimation();
      graph._destructor();
    };
  }, [knowledge, theme, onNodeClick, onLinkClick]);

  const handleZoomIn = () => {
    if (graphRef.current) {
      const newZoom = zoom * 1.2;
      graphRef.current.zoom(newZoom);
      setZoom(newZoom);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      const newZoom = zoom / 1.2;
      graphRef.current.zoom(newZoom);
      setZoom(newZoom);
    }
  };

  const handleCenter = () => {
    if (graphRef.current) {
      graphRef.current.centerAt(0, 0, 0);
      graphRef.current.zoom(1);
      setZoom(1);
    }
  };

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
          position: 'relative',
        }}
      >
        <Typography variant="h6" gutterBottom>
          Knowledge Graph
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

        {isLoading && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
            }}
          >
            <CircularProgress />
          </Box>
        )}

        <Box
          sx={{
            position: 'absolute',
            bottom: 16,
            right: 16,
            display: 'flex',
            gap: 1,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            borderRadius: 1,
            p: 1,
          }}
        >
          <Tooltip title="Zoom In" TransitionComponent={Zoom}>
            <IconButton onClick={handleZoomIn} size="small">
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom Out" TransitionComponent={Zoom}>
            <IconButton onClick={handleZoomOut} size="small">
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Center View" TransitionComponent={Zoom}>
            <IconButton onClick={handleCenter} size="small">
              <CenterFocusStrongIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>
    </motion.div>
  );
};

export default KnowledgeGraph;

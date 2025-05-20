import React, { useState, useEffect, useRef } from "react";
import { Box, useTheme } from "@mui/material";
import { motion } from "framer-motion";

/**
 * Composant d'avatar visuel pour Lucie
 * Inspiré du style Jarvis d'Iron Man, avec des animations réactives
 */
const LucieAvatar = ({
  state = "neutral",
  size = 300,
  pulseIntensity = 0.8,
}) => {
  const theme = useTheme();
  const [blinking, setBlinking] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [processingLevel, setProcessingLevel] = useState(0);
  const animationRef = useRef(null);

  // Couleurs en fonction de l'état
  const getStateColors = () => {
    switch (state) {
      case "thinking":
        return {
          primary: theme.palette.secondary.main,
          secondary: theme.palette.secondary.light,
          accent: theme.palette.secondary.dark,
          glow: `0 0 ${size * 0.1}px ${theme.palette.secondary.main}`,
        };
      case "speaking":
        return {
          primary: theme.palette.info.main,
          secondary: theme.palette.info.light,
          accent: theme.palette.info.dark,
          glow: `0 0 ${size * 0.15}px ${theme.palette.info.main}`,
        };
      case "processing":
        return {
          primary: theme.palette.primary.main,
          secondary: theme.palette.primary.light,
          accent: theme.palette.primary.dark,
          glow: `0 0 ${size * 0.12}px ${theme.palette.primary.main}`,
        };
      case "error":
        return {
          primary: theme.palette.error.main,
          secondary: theme.palette.error.light,
          accent: theme.palette.error.dark,
          glow: `0 0 ${size * 0.12}px ${theme.palette.error.main}`,
        };
      case "idle":
        return {
          primary: "rgba(140, 94, 255, 0.6)",
          secondary: "rgba(140, 94, 255, 0.3)",
          accent: "rgba(140, 94, 255, 0.2)",
          glow: `0 0 ${size * 0.05}px rgba(140, 94, 255, 0.6)`,
        };
      case "neutral":
      default:
        return {
          primary: theme.palette.secondary.main,
          secondary: theme.palette.secondary.light,
          accent: theme.palette.primary.main,
          glow: `0 0 ${size * 0.08}px ${theme.palette.secondary.main}`,
        };
    }
  };

  const colors = getStateColors();

  // Simuler le clignement des yeux
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlinking(true);
      setTimeout(() => setBlinking(false), 200);
    }, Math.random() * 5000 + 3000); // Clignement toutes les 3-8 secondes

    return () => clearInterval(blinkInterval);
  }, []);

  // Gérer l'animation en fonction de l'état
  useEffect(() => {
    setThinking(state === "thinking" || state === "processing");
    setSpeaking(state === "speaking");

    // Animation de "processing"
    let processingAnimation;

    if (state === "processing") {
      processingAnimation = setInterval(() => {
        setProcessingLevel((prev) => (prev + 1) % 100);
      }, 100);
    }

    return () => {
      if (processingAnimation) clearInterval(processingAnimation);
    };
  }, [state]);

  // Dessiner l'animation des particules (effet Jarvis)
  useEffect(() => {
    if (!thinking) return;

    const canvas = animationRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const particles = [];
    const particleCount = 30;

    // Créer les particules
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 2 + 1,
        color: colors.secondary,
        speedX: Math.random() * 2 - 1,
        speedY: Math.random() * 2 - 1,
        life: Math.random() * 100,
      });
    }

    // Animation des particules
    let animationFrame;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p, index) => {
        p.life -= 0.5;

        if (p.life <= 0) {
          p.x = Math.random() * canvas.width;
          p.y = Math.random() * canvas.height;
          p.life = Math.random() * 100;
        }

        p.x += p.speedX;
        p.y += p.speedY;

        // Rebondir sur les bords
        if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
        if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;

        // Dessiner la particule
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.life / 100;
        ctx.fill();

        // Connecter les particules proches
        for (let j = index + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 80) {
            ctx.beginPath();
            ctx.strokeStyle = colors.secondary;
            ctx.globalAlpha = (1 - distance / 80) * 0.5 * (p.life / 100);
            ctx.lineWidth = 0.5;
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      });

      animationFrame = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [thinking, colors]);

  // Définition des variantes d'animation pour framer-motion
  const circleVariants = {
    idle: {
      scale: [1, 1.02, 1],
      transition: {
        duration: 4,
        repeat: Infinity,
        ease: "easeInOut",
      },
    },
    speaking: {
      scale: [1, 1.05, 0.98, 1.03, 1],
      transition: {
        duration: 1.5,
        repeat: Infinity,
        ease: "easeInOut",
      },
    },
    thinking: {
      scale: [1, 1.03, 1, 1.02, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut",
      },
    },
    processing: {
      scale: [1, 1.04, 0.99, 1.02, 1],
      transition: {
        duration: 1.2,
        repeat: Infinity,
        ease: "easeInOut",
      },
    },
    error: {
      scale: [1, 1.1, 0.95, 1.05, 1],
      transition: {
        duration: 0.8,
        repeat: Infinity,
        ease: "easeInOut",
      },
    },
  };

  // Rendu du cercle extérieur (aura)
  const renderOuterCircle = () => (
    <motion.circle
      cx={size / 2}
      cy={size / 2}
      r={size * 0.45}
      fill="none"
      stroke={colors.primary}
      strokeWidth={2}
      strokeDasharray={`${size * 0.08} ${size * 0.03}`}
      variants={circleVariants}
      animate={state}
      style={{
        filter: `drop-shadow(0 0 ${size * 0.04}px ${colors.primary})`,
        opacity: pulseIntensity,
      }}
    />
  );

  // Rendu du cercle intérieur
  const renderInnerCircle = () => (
    <motion.circle
      cx={size / 2}
      cy={size / 2}
      r={size * 0.35}
      fill="none"
      stroke={colors.secondary}
      strokeWidth={1.5}
      animate={{
        opacity: [0.6, 0.9, 0.6],
        strokeDashoffset: [0, size * 2],
      }}
      style={{
        strokeDasharray: size,
        filter: `drop-shadow(0 0 ${size * 0.02}px ${colors.secondary})`,
      }}
      transition={{
        duration: 15,
        repeat: Infinity,
        ease: "linear",
      }}
    />
  );

  // Rendu des yeux
  const renderEyes = () => (
    <g>
      <motion.ellipse
        cx={size * 0.425}
        cy={size * 0.42}
        rx={size * 0.04}
        ry={blinking ? size * 0.001 : size * 0.04}
        fill={colors.secondary}
        animate={{
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          filter: `drop-shadow(0 0 ${size * 0.02}px ${colors.secondary})`,
        }}
      />
      <motion.ellipse
        cx={size * 0.575}
        cy={size * 0.42}
        rx={size * 0.04}
        ry={blinking ? size * 0.001 : size * 0.04}
        fill={colors.secondary}
        animate={{
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          filter: `drop-shadow(0 0 ${size * 0.02}px ${colors.secondary})`,
        }}
      />
    </g>
  );

  // Rendu de la bouche
  const renderMouth = () => {
    // Forme de la bouche en fonction de l'état
    let d = `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.58} ${
      size * 0.6
    },${size * 0.58}`;

    if (speaking) {
      // Bouche parlante (animation)
      return (
        <motion.path
          d={d}
          stroke={colors.secondary}
          strokeWidth={1.5}
          fill="none"
          animate={{
            d: [
              `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.58} ${
                size * 0.6
              },${size * 0.58}`,
              `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.62} ${
                size * 0.6
              },${size * 0.58}`,
              `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.56} ${
                size * 0.6
              },${size * 0.58}`,
              `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.6} ${
                size * 0.6
              },${size * 0.58}`,
              `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.58} ${
                size * 0.6
              },${size * 0.58}`,
            ],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{
            filter: `drop-shadow(0 0 ${size * 0.01}px ${colors.secondary})`,
          }}
        />
      );
    }

    if (state === "thinking") {
      // Bouche réfléchie (légèrement courbée vers le bas)
      d = `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.6} ${
        size * 0.6
      },${size * 0.58}`;
    } else if (state === "error") {
      // Bouche préoccupée (courbée vers le bas)
      d = `M${size * 0.4},${size * 0.6} Q${size * 0.5},${size * 0.56} ${
        size * 0.6
      },${size * 0.6}`;
    } else if (state === "idle") {
      // Bouche neutre
      d = `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.58} ${
        size * 0.6
      },${size * 0.58}`;
    } else if (state === "neutral") {
      // Bouche légèrement souriante
      d = `M${size * 0.4},${size * 0.58} Q${size * 0.5},${size * 0.56} ${
        size * 0.6
      },${size * 0.58}`;
    }

    return (
      <motion.path
        d={d}
        stroke={colors.secondary}
        strokeWidth={1.5}
        fill="none"
        animate={{
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          filter: `drop-shadow(0 0 ${size * 0.01}px ${colors.secondary})`,
        }}
      />
    );
  };

  // Rendu des éléments techniques (style Jarvis)
  const renderTechElements = () => (
    <g>
      {/* Lignes horizontales */}
      <motion.line
        x1={size * 0.1}
        y1={size * 0.2}
        x2={size * 0.3}
        y2={size * 0.2}
        stroke={colors.accent}
        strokeWidth={1}
        animate={{
          opacity: [0.2, 0.8, 0.2],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.line
        x1={size * 0.7}
        y1={size * 0.2}
        x2={size * 0.9}
        y2={size * 0.2}
        stroke={colors.accent}
        strokeWidth={1}
        animate={{
          opacity: [0.2, 0.8, 0.2],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          delay: 0.5,
          ease: "easeInOut",
        }}
      />

      {/* Textes d'accompagnement */}
      {thinking && (
        <>
          <text
            x={size * 0.1}
            y={size * 0.15}
            fill={colors.secondary}
            style={{ fontSize: size * 0.025, opacity: 0.7 }}
          >
            PROCESSING
          </text>
          <motion.text
            x={size * 0.75}
            y={size * 0.15}
            fill={colors.secondary}
            style={{ fontSize: size * 0.025 }}
            animate={{
              opacity: [0.4, 0.8, 0.4],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            {processingLevel}%
          </motion.text>
        </>
      )}

      {/* Cercles de coins */}
      <motion.circle
        cx={size * 0.15}
        cy={size * 0.85}
        r={size * 0.02}
        fill="none"
        stroke={colors.accent}
        strokeWidth={1}
        animate={{
          opacity: [0.3, 0.7, 0.3],
          r: [size * 0.02, size * 0.025, size * 0.02],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.circle
        cx={size * 0.85}
        cy={size * 0.85}
        r={size * 0.02}
        fill="none"
        stroke={colors.accent}
        strokeWidth={1}
        animate={{
          opacity: [0.3, 0.7, 0.3],
          r: [size * 0.02, size * 0.025, size * 0.02],
        }}
        transition={{
          duration: 3,
          delay: 1.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
    </g>
  );

  // Rendu du cercle d'état (indicateur visuel)
  const renderStatusIndicator = () => (
    <motion.circle
      cx={size * 0.5}
      cy={size * 0.78}
      r={size * 0.03}
      fill={colors.primary}
      animate={{
        opacity: [0.7, 1, 0.7],
        scale: [1, 1.1, 1],
      }}
      transition={{
        duration: state === "processing" ? 0.8 : 2,
        repeat: Infinity,
        ease: "easeInOut",
      }}
      style={{
        filter: `drop-shadow(0 0 ${size * 0.01}px ${colors.primary})`,
      }}
    />
  );

  return (
    <Box
      sx={{
        width: size,
        height: size,
        position: "relative",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Canvas pour les animations de particules */}
      <canvas
        ref={animationRef}
        width={size}
        height={size}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          opacity: thinking ? 1 : 0,
          transition: "opacity 0.5s ease",
        }}
      />

      {/* SVG principal pour l'avatar */}
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{
          filter: colors.glow,
          position: "relative",
          zIndex: 2,
        }}
      >
        {renderOuterCircle()}
        {renderInnerCircle()}
        {renderEyes()}
        {renderMouth()}
        {renderTechElements()}
        {renderStatusIndicator()}
      </svg>
    </Box>
  );
};

export default LucieAvatar;

import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";

/**
 * Composant d'avatar visuel amélioré pour Lucie
 * Basé sur le design décrit dans la documentation
 * @param {Object} props - Propriétés du composant
 * @param {string} props.state - État émotionnel de l'avatar ('neutral', 'thinking', 'speaking', 'processing', 'error')
 * @param {number} props.size - Taille de l'avatar en pixels
 * @param {number} props.pulseIntensity - Intensité de l'effet de pulsation (0-1)
 */
const LucieAvatarEnhanced = ({
  state = "neutral",
  size = 300,
  pulseIntensity = 0.8,
}) => {
  const [blinking, setBlinking] = useState(false);
  const [processingLevel, setProcessingLevel] = useState(0);
  const canvasRef = useRef(null);
  const networkRef = useRef(null);

  // Couleurs en fonction de l'état
  const getStateColors = () => {
    switch (state) {
      case "thinking":
        return {
          primary: "#8c5eff", // Violet principal
          secondary: "#b38fff", // Violet plus clair
          accent: "#6a35e0", // Violet plus foncé
          glow: `0 0 ${size * 0.1}px #8c5eff`,
          particles: {
            color: "#b38fff",
            speed: 0.7,
          },
        };
      case "speaking":
        return {
          primary: "#36e7fc", // Bleu cyan
          secondary: "#5aeeff", // Bleu cyan clair
          accent: "#00d4ff", // Bleu cyan foncé
          glow: `0 0 ${size * 0.15}px #36e7fc`,
          particles: {
            color: "#5aeeff",
            speed: 1.2,
          },
        };
      case "processing":
        return {
          primary: "#a988ff", // Violet clair
          secondary: "#c9b5ff", // Violet très clair
          accent: "#9061ff", // Violet moyen
          glow: `0 0 ${size * 0.12}px #a988ff`,
          particles: {
            color: "#c9b5ff",
            speed: 1.5,
          },
        };
      case "error":
        return {
          primary: "#ff3d71", // Rouge vif
          secondary: "#ff6b94", // Rouge clair
          accent: "#e91a56", // Rouge foncé
          glow: `0 0 ${size * 0.12}px #ff3d71`,
          particles: {
            color: "#ff6b94",
            speed: 2.0,
          },
        };
      case "listening":
        return {
          primary: "#00d68f", // Vert
          secondary: "#39e8b0", // Vert clair
          accent: "#00b377", // Vert foncé
          glow: `0 0 ${size * 0.12}px #00d68f`,
          particles: {
            color: "#39e8b0",
            speed: 0.8,
          },
        };
      case "idle":
        return {
          primary: "rgba(140, 94, 255, 0.6)", // Violet transparent
          secondary: "rgba(140, 94, 255, 0.3)", // Violet très transparent
          accent: "rgba(140, 94, 255, 0.2)", // Violet presque transparent
          glow: `0 0 ${size * 0.05}px rgba(140, 94, 255, 0.6)`,
          particles: {
            color: "rgba(140, 94, 255, 0.3)",
            speed: 0.4,
          },
        };
      case "neutral":
      default:
        return {
          primary: "#8c5eff", // Violet principal
          secondary: "#b38fff", // Violet plus clair
          accent: "#e6f7ff", // Bleu très clair (pour les détails angéliques)
          glow: `0 0 ${size * 0.08}px #8c5eff`,
          particles: {
            color: "#b38fff",
            speed: 0.5,
          },
        };
    }
  };

  const colors = getStateColors();
  const isThinking = state === "thinking" || state === "processing";
  const isSpeaking = state === "speaking";

  // Simuler le clignement des yeux
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setBlinking(true);
      setTimeout(() => setBlinking(false), 200);
    }, Math.random() * 5000 + 3000); // Clignement toutes les 3-8 secondes

    return () => clearInterval(blinkInterval);
  }, []);

  // Animation de "processing"
  useEffect(() => {
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

  // Dessiner l'animation des cheveux en réseau (style angélique)
  useEffect(() => {
    const canvas = networkRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    // Configuration du réseau
    const centerX = width / 2;
    const centerY = height / 2.5; // Un peu plus haut pour ressembler à des cheveux
    const nodeCount = 30;
    const maxDistance = size * 0.45; // Rayon maximum des liens
    const nodes = [];

    // Créer les nœuds du réseau (points de connexion)
    for (let i = 0; i < nodeCount; i++) {
      // Répartition plus concentrée autour du visage mais qui s'étend vers le haut et les côtés
      const angle = Math.random() * Math.PI * 1.2 - Math.PI * 0.6; // -60° à +60°
      const distance = Math.random() * size * 0.6;

      nodes.push({
        x: centerX + Math.cos(angle) * distance,
        y: centerY - Math.abs(Math.sin(angle) * distance) * 0.7, // Vers le haut principalement
        size: Math.random() * 2 + 1,
        speed: {
          x: (Math.random() - 0.5) * 0.5,
          y: (Math.random() - 0.5) * 0.5,
        },
        brightness: Math.random() * 0.5 + 0.2, // Variation de luminosité
        processing: Math.random(), // Phase pour l'animation de traitement
      });
    }

    // Fonction d'animation
    let animationFrame;
    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      // Mettre à jour et dessiner les nœuds
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        // Animation différente selon l'état
        if (isThinking) {
          // Mouvement plus rapide et énergique pendant la réflexion
          node.x += node.speed.x * colors.particles.speed * 2;
          node.y += node.speed.y * colors.particles.speed * 2;

          // Effet de pulsation pendant le traitement
          node.processing += 0.01;
          node.brightness = 0.2 + Math.abs(Math.sin(node.processing)) * 0.7;
        } else if (isSpeaking) {
          // Ondulation pendant la parole
          node.x += Math.sin(Date.now() * 0.001 + i) * 0.3;
          node.y += Math.cos(Date.now() * 0.001 + i) * 0.3;
          node.brightness = 0.4 + Math.sin(Date.now() * 0.003 + i * 0.5) * 0.3;
        } else {
          // Mouvement léger en état normal
          node.x += node.speed.x * 0.5;
          node.y += node.speed.y * 0.5;
          node.brightness = 0.2 + Math.sin(Date.now() * 0.001 + i * 0.2) * 0.1;
        }

        // Garder les nœuds dans les limites d'un ovale autour du visage
        const dx = node.x - centerX;
        const dy = node.y - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const maxRadiusX = size * 0.4;
        const maxRadiusY = size * 0.6;

        if (distance > maxRadiusX || Math.abs(dy) > maxRadiusY) {
          // Rediriger vers le centre avec une composante aléatoire
          node.speed.x =
            (centerX - node.x) * 0.01 + (Math.random() - 0.5) * 0.2;
          node.speed.y =
            (centerY - node.y) * 0.01 + (Math.random() - 0.5) * 0.2;
        }

        // Dessiner le nœud (point lumineux)
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${hexToRgb(colors.secondary)}, ${
          node.brightness
        })`;
        ctx.fill();
      }

      // Dessiner les connexions entre les nœuds (cheveux en réseau)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const nodeA = nodes[i];
          const nodeB = nodes[j];
          const dx = nodeA.x - nodeB.x;
          const dy = nodeA.y - nodeB.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < maxDistance) {
            // Calculer l'opacité basée sur la distance
            const opacity =
              (1 - distance / maxDistance) *
              0.5 *
              nodeA.brightness *
              nodeB.brightness;

            // Dessiner la ligne
            ctx.beginPath();
            ctx.moveTo(nodeA.x, nodeA.y);
            ctx.lineTo(nodeB.x, nodeB.y);
            ctx.strokeStyle = `rgba(${hexToRgb(colors.secondary)}, ${opacity})`;
            ctx.lineWidth = Math.max(0.5, (1 - distance / maxDistance) * 2);
            ctx.stroke();
          }
        }
      }

      animationFrame = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [isThinking, isSpeaking, colors, size]);

  // Dessiner l'animation des particules (effet Jarvis)
  useEffect(() => {
    if (!isThinking) return;

    const canvas = canvasRef.current;
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
        color: colors.particles.color,
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

        p.x += p.speedX * colors.particles.speed;
        p.y += p.speedY * colors.particles.speed;

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
  }, [isThinking, colors]);

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

  // Rendu du cercle extérieur (aura angélique)
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

    if (isSpeaking) {
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
      d = `M${size * 0.4},${size * 0.6} Q${size * 0.5},${size * 0.64} ${
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
      {isThinking && (
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

  // Fonction utilitaire pour convertir hex en rgb
  const hexToRgb = (hex) => {
    // Supprimer le # si présent
    hex = hex.replace(/^#/, "");

    // Convertir 3 caractères en 6 caractères
    if (hex.length === 3) {
      hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }

    // Convertir en RGB
    const bigint = parseInt(hex, 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;

    return `${r}, ${g}, ${b}`;
  };

  // Rendu du halo angélique
  const renderHalo = () => (
    <motion.circle
      cx={size / 2}
      cy={size / 2}
      r={size * 0.3}
      fill="none"
      stroke={colors.accent}
      strokeWidth={1}
      strokeDasharray={`${size * 0.01} ${size * 0.01}`}
      animate={{
        opacity: [0.3, 0.6, 0.3],
        scale: [1, 1.05, 1],
      }}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut",
      }}
      style={{
        filter: `drop-shadow(0 0 ${size * 0.03}px ${colors.accent})`,
      }}
    />
  );

  return (
    <div
      style={{
        width: size,
        height: size,
        position: "relative",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Canvas pour l'animation des cheveux en réseau angélique */}
      <canvas
        ref={networkRef}
        width={size}
        height={size}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          zIndex: 1,
        }}
      />

      {/* Canvas pour les animations de particules */}
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          opacity: isThinking ? 1 : 0,
          transition: "opacity 0.5s ease",
          zIndex: 2,
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
          zIndex: 3,
        }}
      >
        {renderHalo()}
        {renderOuterCircle()}
        {renderInnerCircle()}
        {renderEyes()}
        {renderMouth()}
        {renderTechElements()}
        {renderStatusIndicator()}
      </svg>
    </div>
  );
};

export default LucieAvatarEnhanced;

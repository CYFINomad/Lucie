/**
 * Utilitaires et fonctions d'aide pour Lucie
 * Fournit des fonctions réutilisables pour l'ensemble de l'application
 */

/**
 * Détermine l'état de l'avatar en fonction du message
 * @param {string} message - Message à analyser
 * @returns {string} État de l'avatar approprié
 */
export const determineAvatarState = (message) => {
  if (!message) return "neutral";

  // Détection d'une question
  if (message.includes("?")) return "thinking";

  // Détection d'une exclamation
  if (message.includes("!")) return "speaking";

  // Par défaut
  return "neutral";
};

/**
 * Détermine l'état de l'avatar en fonction de l'intention
 * @param {string} intent - Intention détectée
 * @param {number} confidence - Niveau de confiance
 * @returns {string} État de l'avatar approprié
 */
export const getAvatarStateFromIntent = (intent, confidence = 1.0) => {
  // Si l'intention n'est pas définie ou la confiance est faible
  if (!intent || confidence < 0.5) return "neutral";

  // Correspondance d'intention à état
  const intentStateMap = {
    "conversation.greeting": "speaking",
    "conversation.farewell": "neutral",
    "conversation.thanks": "speaking",
    "conversation.help": "thinking",
    "system.status": "processing",
    question: "thinking",
    fallback: "neutral",
    error: "error",
  };

  // Extraire la catégorie principale de l'intention
  const category = intent.split(".")[0];

  // Vérifier si l'intention spécifique existe dans la map
  if (intentStateMap[intent]) {
    return intentStateMap[intent];
  }

  // Vérifier si la catégorie existe dans la map
  if (intentStateMap[category]) {
    return intentStateMap[category];
  }

  // Par défaut
  return "neutral";
};

/**
 * Calcule la durée d'affichage recommandée pour un message
 * @param {string} message - Message à afficher
 * @returns {number} Durée en millisecondes
 */
export const calculateReadingTime = (message) => {
  if (!message) return 0;

  // Moyenne de lecture: ~200 mots par minute, soit ~3.33 mots par seconde
  // Soit environ 300ms par mot en moyenne
  const words = message.split(/\s+/).length;
  const baseTime = words * 300;

  // Minimum 1 seconde, maximum 10 secondes
  return Math.max(1000, Math.min(baseTime, 10000));
};

/**
 * Masque partiellement un texte sensible
 * @param {string} text - Texte à masquer
 * @param {number} visibleStart - Nombre de caractères visibles au début
 * @param {number} visibleEnd - Nombre de caractères visibles à la fin
 * @returns {string} Texte masqué
 */
export const maskSensitiveText = (text, visibleStart = 4, visibleEnd = 4) => {
  if (!text) return "";
  if (text.length <= visibleStart + visibleEnd) return text;

  const start = text.substring(0, visibleStart);
  const end = text.substring(text.length - visibleEnd);
  const masked = "*".repeat(
    Math.min(10, text.length - (visibleStart + visibleEnd))
  );

  return `${start}${masked}${end}`;
};

/**
 * Formatte une date en fonction de la locale
 * @param {string|Date} date - Date à formatter
 * @param {Object} options - Options de formatage
 * @returns {string} Date formattée
 */
export const formatDate = (date, options = {}) => {
  if (!date) return "";

  const dateObj = typeof date === "string" ? new Date(date) : date;

  // Options par défaut
  const defaultOptions = {
    dateStyle: "medium",
    timeStyle: "short",
  };

  // Fusionner les options
  const mergedOptions = { ...defaultOptions, ...options };

  // Formatter la date
  try {
    return new Intl.DateTimeFormat("fr-FR", mergedOptions).format(dateObj);
  } catch (error) {
    console.error("Erreur lors du formatage de la date:", error);
    return dateObj.toLocaleString("fr-FR");
  }
};

/**
 * Génère un identifiant unique
 * @param {string} prefix - Préfixe de l'identifiant
 * @returns {string} Identifiant unique
 */
export const generateId = (prefix = "lucie") => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Détermine la gravité d'une erreur
 * @param {Error|string} error - Erreur à analyser
 * @returns {string} Niveau de gravité ('high', 'medium', 'low')
 */
export const determineErrorSeverity = (error) => {
  if (!error) return "low";

  const errorStr = error.message || error.toString();

  // Erreurs critiques
  if (
    errorStr.includes("connexion") ||
    errorStr.includes("réseau") ||
    errorStr.includes("authentification") ||
    errorStr.includes("serveur") ||
    errorStr.includes("timeout") ||
    errorStr.includes("délai")
  ) {
    return "high";
  }

  // Erreurs moyennes
  if (
    errorStr.includes("données") ||
    errorStr.includes("processus") ||
    errorStr.includes("traitement") ||
    errorStr.includes("temporaire")
  ) {
    return "medium";
  }

  // Erreurs légères
  return "low";
};

/**
 * Détecte si un texte est probablement du code
 * @param {string} text - Texte à analyser
 * @returns {boolean} Vrai si le texte contient probablement du code
 */
export const containsCode = (text) => {
  if (!text) return false;

  // Marqueurs de code
  const codeMarkers = [
    "```", // Bloc de code Markdown
    "function", // JavaScript/TypeScript
    "const ", // JavaScript/TypeScript
    "let ", // JavaScript/TypeScript
    "var ", // JavaScript/TypeScript
    "import ", // JavaScript/TypeScript/Python
    "class ", // JavaScript/TypeScript/Python
    "def ", // Python
    "if ", // Divers
    "for ", // Divers
    "while ", // Divers
    "{", // JSON/Objets
    "}", // JSON/Objets
    "};", // JavaScript/TypeScript
    ");", // JavaScript/TypeScript
    "return ", // JavaScript/TypeScript
    "<?php", // PHP
    "#include", // C/C++
    "public static void", // Java
  ];

  // Vérifier si le texte contient au moins un marqueur de code
  return codeMarkers.some((marker) => text.includes(marker));
};

/**
 * Détermine le langage de programmation d'un bloc de code
 * @param {string} code - Code à analyser
 * @returns {string} Langage de programmation détecté
 */
export const detectCodeLanguage = (code) => {
  if (!code) return "javascript";

  // Marqueurs de langages
  const languageMarkers = {
    python: ["def ", "import ", "from ", "class ", "if __name__ =="],
    javascript: [
      "const ",
      "let ",
      "var ",
      "function",
      "export ",
      "import {",
      "require(",
    ],
    typescript: [
      "interface ",
      "type ",
      "<T>",
      ":string",
      ":number",
      ":boolean",
    ],
    html: ["<!DOCTYPE", "<html", "<div", "<body", "<head"],
    css: ["{", "}", "margin:", "padding:", "color:", "background:"],
    java: ["public class", "private", "protected", "extends", "implements"],
    c: ["#include", "int main(", "stdio.h", "void", "char *"],
    cpp: ["#include", "namespace", "::"],
    php: ["<?php", "?>", "echo", "$_"],
    ruby: ["def ", "end", "require ", "class ", "attr_"],
    sql: ["SELECT", "FROM", "WHERE", "JOIN", "INSERT", "UPDATE", "DELETE"],
  };

  // Vérifier pour chaque langage
  for (const [language, markers] of Object.entries(languageMarkers)) {
    const matchCount = markers.filter((marker) => code.includes(marker)).length;

    if (matchCount >= 2) {
      return language;
    }
  }

  // Langage par défaut
  return "javascript";
};

export default {
  determineAvatarState,
  getAvatarStateFromIntent,
  calculateReadingTime,
  maskSensitiveText,
  formatDate,
  generateId,
  determineErrorSeverity,
  containsCode,
  detectCodeLanguage,
};

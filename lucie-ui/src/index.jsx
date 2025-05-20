import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

/**
 * Point d'entrée principal de Lucie UI
 * Monte l'application React dans l'élément racine
 */
const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Informations de débogage en mode développement
if (process.env.NODE_ENV === "development") {
  console.log(
    "%cLucie UI%c - Mode développement",
    "color: #8c5eff; font-size: 20px; font-weight: bold;",
    "color: #f5f5f5; font-size: 16px;"
  );
}

// Prévenir les fuites de mémoire
if (module.hot) {
  module.hot.accept();
}

#!/usr/bin/env node
/**
 * Script pour configurer l'environnement VS Code pour Lucie
 * Installe les extensions recommandées et vérifie la configuration
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const readline = require("readline");

// Couleurs pour les messages
const GREEN = "\x1b[32m";
const BLUE = "\x1b[34m";
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const RESET = "\x1b[0m";

// Utilitaires
const log = {
  info: (msg) => console.log(`${BLUE}INFO${RESET}: ${msg}`),
  success: (msg) => console.log(`${GREEN}SUCCESS${RESET}: ${msg}`),
  error: (msg) => console.log(`${RED}ERROR${RESET}: ${msg}`),
  warning: (msg) => console.log(`${YELLOW}WARNING${RESET}: ${msg}`),
};

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

// Vérifie si VS Code est installé
function checkVSCodeInstalled() {
  try {
    execSync("code --version", { stdio: "ignore" });
    return true;
  } catch (error) {
    return false;
  }
}

// Installe une extension VS Code
function installExtension(extensionId) {
  try {
    log.info(`Installation de l'extension ${extensionId}...`);
    execSync(`code --install-extension ${extensionId}`, { stdio: "ignore" });
    return true;
  } catch (error) {
    log.error(
      `Erreur lors de l'installation de ${extensionId}: ${error.message}`
    );
    return false;
  }
}

// Vérifie si un fichier existe
function checkFileExists(filePath) {
  return fs.existsSync(filePath);
}

// Crée un répertoire s'il n'existe pas
function ensureDirectoryExists(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    log.info(`Répertoire ${dirPath} créé.`);
  }
}

// Crée un fichier de configuration VS Code
function createConfigFile(filePath, content) {
  try {
    ensureDirectoryExists(path.dirname(filePath));
    fs.writeFileSync(filePath, JSON.stringify(content, null, 2));
    log.success(`Fichier ${filePath} créé.`);
    return true;
  } catch (error) {
    log.error(`Erreur lors de la création de ${filePath}: ${error.message}`);
    return false;
  }
}

// Demande une confirmation à l'utilisateur
async function askConfirmation(question) {
  return new Promise((resolve) => {
    rl.question(`${question} (y/n) `, (answer) => {
      resolve(answer.toLowerCase() === "y" || answer.toLowerCase() === "yes");
    });
  });
}

// Configuration principale
async function setupVSCode() {
  log.info("Vérification de l'installation de VS Code...");
  if (!checkVSCodeInstalled()) {
    log.error("VS Code n'est pas installé ou n'est pas dans le PATH.");
    log.info(
      "Veuillez installer VS Code et vous assurer qu'il est dans le PATH."
    );
    rl.close();
    return;
  }
  log.success("VS Code est installé.");

  // Charger les extensions recommandées
  const rootDir = path.resolve(__dirname, "../..");
  const extensionsJsonPath = path.join(rootDir, ".vscode", "extensions.json");
  const launchJsonPath = path.join(rootDir, ".vscode", "launch.json");
  const tasksJsonPath = path.join(rootDir, ".vscode", "tasks.json");
  const settingsJsonPath = path.join(rootDir, ".vscode", "settings.json");
  const devContainerJsonPath = path.join(
    rootDir,
    ".devcontainer",
    "devcontainer.json"
  );

  // Créer les fichiers de configuration VS Code
  const extensionsJson = require(extensionsJsonPath);
  const recommendations = extensionsJson.recommendations || [];

  if (recommendations.length > 0) {
    log.info(`${recommendations.length} extensions recommandées trouvées.`);
    const shouldInstall = await askConfirmation(
      "Voulez-vous installer les extensions recommandées?"
    );

    if (shouldInstall) {
      let successCount = 0;
      for (const extension of recommendations) {
        if (installExtension(extension)) {
          successCount++;
        }
      }
      log.success(
        `${successCount}/${recommendations.length} extensions installées avec succès.`
      );
    }
  }

  // Vérifier et créer les autres fichiers de configuration
  const configFiles = [
    { path: launchJsonPath, name: "launch.json" },
    { path: tasksJsonPath, name: "tasks.json" },
    { path: settingsJsonPath, name: "settings.json" },
    { path: devContainerJsonPath, name: "devcontainer.json" },
  ];

  for (const file of configFiles) {
    if (!checkFileExists(file.path)) {
      log.warning(`Le fichier ${file.name} n'existe pas.`);
      const shouldCreate = await askConfirmation(
        `Voulez-vous créer le fichier ${file.name}?`
      );

      if (shouldCreate) {
        // Dans une vraie implémentation, il faudrait avoir le contenu des fichiers
        log.info(
          `Veuillez créer manuellement le fichier ${file.path} avec le contenu approprié.`
        );
      }
    } else {
      log.success(`Le fichier ${file.name} existe.`);
    }
  }

  log.info("Vérification des dépendances Node.js...");
  try {
    const backendPackageJsonPath = path.join(
      rootDir,
      "backend",
      "package.json"
    );
    const uiPackageJsonPath = path.join(rootDir, "lucie-ui", "package.json");

    if (
      checkFileExists(backendPackageJsonPath) &&
      checkFileExists(uiPackageJsonPath)
    ) {
      log.success("Fichiers package.json trouvés.");
      const shouldInstall = await askConfirmation(
        "Voulez-vous installer les dépendances Node.js?"
      );

      if (shouldInstall) {
        log.info("Installation des dépendances backend...");
        execSync("cd backend && npm install", { stdio: "inherit" });

        log.info("Installation des dépendances frontend...");
        execSync("cd lucie-ui && npm install", { stdio: "inherit" });

        log.success("Dépendances Node.js installées avec succès.");
      }
    } else {
      log.warning("Certains fichiers package.json sont manquants.");
    }
  } catch (error) {
    log.error(
      `Erreur lors de l'installation des dépendances: ${error.message}`
    );
  }

  log.info("Vérification de l'environnement Python...");
  try {
    const requirementsPath = path.join(
      rootDir,
      "python-ai",
      "requirements.txt"
    );

    if (checkFileExists(requirementsPath)) {
      log.success("Fichier requirements.txt trouvé.");
      const shouldSetup = await askConfirmation(
        "Voulez-vous configurer l'environnement Python?"
      );

      if (shouldSetup) {
        log.info("Création de l'environnement virtuel Python...");
        execSync("cd python-ai && python -m venv venv", { stdio: "inherit" });

        log.info("Installation des dépendances Python...");
        if (process.platform === "win32") {
          execSync(
            "cd python-ai && .\\venv\\Scripts\\pip install -r requirements.txt",
            { stdio: "inherit" }
          );
        } else {
          execSync(
            "cd python-ai && ./venv/bin/pip install -r requirements.txt",
            { stdio: "inherit" }
          );
        }

        log.success("Environnement Python configuré avec succès.");
      }
    } else {
      log.warning("Fichier requirements.txt manquant.");
    }
  } catch (error) {
    log.error(
      `Erreur lors de la configuration de l'environnement Python: ${error.message}`
    );
  }

  log.success("Configuration de l'environnement VS Code terminée.");
  log.info(
    "Vous pouvez maintenant ouvrir le projet dans VS Code et commencer à développer."
  );
  rl.close();
}

// Exécution principale
setupVSCode().catch((error) => {
  log.error(`Erreur lors de la configuration: ${error.message}`);
  rl.close();
});

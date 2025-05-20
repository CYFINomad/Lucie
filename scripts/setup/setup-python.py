#!/usr/bin/env python3
"""
Script d'initialisation de l'environnement Python pour Lucie
Prépare l'environnement virtuel, installe les dépendances et configure le projet
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

# Couleurs pour les messages (si terminal supporte ANSI)
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


def _print_colored(color, message):
    """Affiche un message coloré"""
    supports_color = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    if supports_color and platform.system() != "Windows":
        print(f"{color}{message}{NC}")
    else:
        print(message)


def info(message):
    """Affiche un message d'information"""
    _print_colored(BLUE, f"INFO: {message}")


def success(message):
    """Affiche un message de succès"""
    _print_colored(GREEN, f"SUCCESS: {message}")


def warning(message):
    """Affiche un message d'avertissement"""
    _print_colored(YELLOW, f"WARNING: {message}")


def error(message):
    """Affiche un message d'erreur"""
    _print_colored(RED, f"ERROR: {message}")


def is_allowed_command(command):
    """Validate if command is in allowed list"""
    allowed_commands = {"pip": ["install", "-r"], "python": ["-m", "venv"]}
    if not command or not isinstance(command, list) or len(command) < 1:
        return False
    cmd = os.path.basename(command[0])
    return cmd in allowed_commands and all(
        arg in allowed_commands[cmd] for arg in command[1:] if not arg.startswith("-")
    )


def run_command(command, cwd=None):
    """
    Exécute une commande shell
    Args:
        command: Liste de commande à exécuter
        cwd: Répertoire de travail pour l'exécution de la commande
    Returns:
        Succès (booléen)
    """
    try:
        if not isinstance(command, list):
            error("Command must be a list of arguments")
            return False

        # Validate command arguments
        for arg in command:
            if not isinstance(arg, str) or not arg.strip():
                error("Invalid command argument")
                return False

        if not is_allowed_command(command):
            error("Command not allowed")
            return False

        result = subprocess.run(
            command, cwd=cwd, check=True, capture_output=True, text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        error(f"Commande '{' '.join(command)}' a échoué avec code {e.returncode}")
        if e.stdout:
            print(f"Sortie standard: {e.stdout}")
        if e.stderr:
            print(f"Erreur standard: {e.stderr}")
        return False


def setup_virtual_env(python_dir, venv_name="venv"):
    """Configure l'environnement virtuel Python"""
    venv_path = os.path.join(python_dir, venv_name)

    if os.path.exists(venv_path):
        warning(f"Environnement virtuel {venv_path} existe déjà.")
        return True

    info(f"Création de l'environnement virtuel dans {venv_path}...")
    return run_command([sys.executable, "-m", "venv", venv_name], cwd=python_dir)


def install_requirements(python_dir, venv_name="venv"):
    """Installe les dépendances Python"""
    requirements_path = os.path.join(python_dir, "requirements.txt")
    if not os.path.exists(requirements_path):
        error(f"Fichier requirements.txt non trouvé dans {python_dir}")
        return False

    if not is_safe_path(python_dir, requirements_path):
        error("Invalid requirements.txt path")
        return False

    # Déterminer le chemin de pip
    if platform.system() == "Windows":
        pip_path = os.path.join(python_dir, venv_name, "Scripts", "pip")
    else:
        pip_path = os.path.join(python_dir, venv_name, "bin", "pip")

    if not is_safe_path(python_dir, pip_path):
        error("Invalid pip path")
        return False

    info("Installation des dépendances...")
    return run_command([pip_path, "install", "-r", requirements_path], cwd=python_dir)


def is_safe_path(base_path, path):
    """Check if path is within base_path directory"""
    base_path = os.path.abspath(base_path)
    path = os.path.abspath(path)
    return os.path.commonpath([base_path]) == os.path.commonpath([base_path, path])


def prepare_python_env(python_dir):
    """Prépare l'environnement Python pour le développement"""
    # Validate base directory
    if not is_safe_path(os.getcwd(), python_dir):
        error("Invalid Python directory path")
        return False

    # Créer les dossiers nécessaires
    for directory in ["logs", "data"]:
        dir_path = os.path.join(python_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            info(f"Dossier {directory} créé.")

    # Créer un fichier .env d'exemple si nécessaire
    env_example = os.path.join(python_dir, ".env.example")
    env_file = os.path.join(python_dir, ".env")

    if not os.path.exists(env_file) and os.path.exists(env_example):
        if not is_safe_path(python_dir, env_example) or not is_safe_path(
            python_dir, env_file
        ):
            error("Invalid file path detected")
            return False
        try:
            with open(env_example, "r") as src, open(env_file, "w") as dst:
                dst.write(src.read())
            info("Fichier .env créé à partir de .env.example")
        except (IOError, OSError) as e:
            error(f"Error copying .env file: {str(e)}")
            return False

    return True


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Configuration de l'environnement Python pour Lucie"
    )
    parser.add_argument(
        "--dir", default="../python-ai", help="Chemin vers le répertoire Python"
    )
    parser.add_argument("--venv", default="venv", help="Nom de l'environnement virtuel")
    args = parser.parse_args()

    # Obtenir le chemin absolu du répertoire Python
    current_dir = Path(__file__).parent.absolute()
    python_dir = os.path.abspath(os.path.join(current_dir, args.dir))

    # Validate that python_dir is within the workspace
    if not is_safe_path(os.getcwd(), python_dir):
        error(f"Invalid directory path: {python_dir} is outside the workspace")
        return 1

    if not os.path.exists(python_dir):
        error(f"Le répertoire {python_dir} n'existe pas.")
        return 1

    info(f"Configuration de l'environnement Python dans {python_dir}...")

    # Créer l'environnement virtuel
    if not setup_virtual_env(python_dir, args.venv):
        return 1

    # Installer les dépendances
    if not install_requirements(python_dir, args.venv):
        return 1

    # Préparer l'environnement
    if not prepare_python_env(python_dir):
        return 1

    success("Configuration de l'environnement Python terminée avec succès.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

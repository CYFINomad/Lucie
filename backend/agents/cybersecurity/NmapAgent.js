/**
 * Agent Nmap pour Lucie
 * Effectue des analyses réseau avec Nmap et traite les résultats
 */

const { spawn } = require("child_process");
const { promisify } = require("util");
const fs = require("fs");
const path = require("path");
const os = require("os");

// Promisification des fonctions fs
const writeFile = promisify(fs.writeFile);
const readFile = promisify(fs.readFile);
const unlink = promisify(fs.unlink);

class NmapAgent {
  /**
   * Crée un nouvel agent Nmap
   */
  constructor() {
    this.id = `nmap_${Date.now()}`;
    this.name = "Nmap Network Scanner";
    this.description =
      "Exécute des scans réseau et analyse des ports et services";
    this.capabilities = [
      "network_scanning",
      "port_discovery",
      "service_detection",
      "os_fingerprinting",
      "script_scanning",
    ];
    this.agent_type = "specialized";
    this.category = "cybersecurity";
    this.active = true;
    this.statistics = {
      scansCompleted: 0,
      scansFailed: 0,
      totalScanTime: 0,
      averageScanTime: 0,
      lastScanTimestamp: null,
    };

    // Configuration par défaut pour Nmap
    this.config = {
      defaultArgs: ["-sS", "-T4"],
      timeoutSeconds: 300, // 5 minutes par défaut
      outputDir: path.join(os.tmpdir(), "lucie-nmap"),
      logScans: true,
    };

    // Créer le répertoire de sortie si nécessaire
    if (!fs.existsSync(this.config.outputDir)) {
      fs.mkdirSync(this.config.outputDir, { recursive: true });
    }

    console.log(`[NmapAgent] Agent créé: ${this.name} (${this.id})`);
  }

  /**
   * Vérifie si l'agent peut traiter une requête
   * @param {string} requestType - Type de requête
   * @param {Object} inputData - Données d'entrée
   * @returns {boolean} Vrai si l'agent peut traiter la requête
   */
  can_handle(request) {
    // Vérifier si l'agent est actif
    if (!this.active) {
      return false;
    }

    // Vérifier si c'est une requête de scan réseau
    if (typeof request !== "object") {
      return false;
    }

    // Vérifier le type de requête
    const supportedTypes = ["network_scan", "port_scan", "service_detection"];
    if (supportedTypes.includes(request.type)) {
      return true;
    }

    // Vérifier si la requête contient des indications de scan réseau
    if (request.content && typeof request.content === "object") {
      const content = request.content;

      // Vérifier si la requête contient des éléments liés au scan réseau
      if (content.target || content.hosts || content.ip || content.network) {
        return true;
      }

      // Vérifier si la requête mentionne explicitement Nmap
      if (
        content.tool === "nmap" ||
        (content.query && content.query.toLowerCase().includes("nmap"))
      ) {
        return true;
      }
    }

    return false;
  }

  /**
   * Traite une requête de scan réseau
   * @param {Object} inputData - Données d'entrée
   * @param {Object} context - Contexte d'exécution
   * @returns {Promise<Object>} Résultats du scan
   */
  async process(request, context = {}) {
    console.log(`[NmapAgent] Traitement de la requête: ${request.type}`);

    const startTime = Date.now();

    try {
      // Extraire les cibles et options
      const { targets, options } = this._extractScanParameters(request);

      // Valider les cibles
      if (!targets || targets.length === 0) {
        throw new Error("Aucune cible valide spécifiée pour le scan");
      }

      // Construire la commande Nmap
      const scanCommand = this._buildScanCommand(targets, options);

      // Exécuter le scan
      const scanResults = await this._executeScan(
        scanCommand.targets,
        scanCommand.args
      );

      // Analyser les résultats
      const parsedResults = this._parseResults(scanResults);

      // Mettre à jour les statistiques
      const scanTime = Date.now() - startTime;
      this.statistics.scansCompleted++;
      this.statistics.totalScanTime += scanTime;
      this.statistics.averageScanTime =
        this.statistics.totalScanTime / this.statistics.scansCompleted;
      this.statistics.lastScanTimestamp = new Date().toISOString();

      // Générer le rapport
      const report = this._generateReport(parsedResults, scanCommand, scanTime);

      console.log(`[NmapAgent] Scan réseau terminé en ${scanTime}ms`);

      return {
        success: true,
        scanId: `scan_${Date.now()}`,
        scanTime,
        command: scanCommand.command,
        summary: parsedResults.summary,
        hosts: parsedResults.hosts,
        rawResults: context.includeRawResults ? scanResults : undefined,
        report,
      };
    } catch (error) {
      console.error(`[NmapAgent] Erreur lors du scan réseau: ${error.message}`);

      // Mettre à jour les statistiques d'erreur
      this.statistics.scansFailed++;

      return {
        success: false,
        error: error.message,
        errorCode: error.code,
        scanId: `scan_failed_${Date.now()}`,
      };
    }
  }

  /**
   * Extrait les paramètres de scan à partir de la requête
   * @param {Object} request - Requête de scan
   * @returns {Object} Cibles et options
   * @private
   */
  _extractScanParameters(request) {
    let targets = [];
    let options = {};

    // Extraire les cibles
    if (request.content) {
      const content = request.content;

      // Récupérer les cibles
      if (content.target) {
        targets.push(content.target);
      } else if (content.hosts && Array.isArray(content.hosts)) {
        targets = targets.concat(content.hosts);
      } else if (content.ip) {
        targets.push(content.ip);
      } else if (content.network) {
        targets.push(content.network);
      }

      // Récupérer les options
      if (content.options && typeof content.options === "object") {
        options = { ...content.options };
      }

      // Options spécifiques
      if (content.ports) {
        options.ports = content.ports;
      }
      if (content.scanType) {
        options.scanType = content.scanType;
      }
      if (content.intensity !== undefined) {
        options.intensity = content.intensity;
      }
      if (content.scripts) {
        options.scripts = content.scripts;
      }
    }

    return { targets, options };
  }

  /**
   * Construit la commande Nmap à exécuter
   * @param {Array} targets - Cibles du scan
   * @param {Object} options - Options du scan
   * @returns {Object} Commande et arguments construits
   * @private
   */
  _buildScanCommand(targets, options = {}) {
    // Arguments de base
    const args = [...this.config.defaultArgs];

    // Type de scan
    if (options.scanType) {
      switch (options.scanType.toLowerCase()) {
        case "syn":
          args.push("-sS");
          break;
        case "connect":
          args.push("-sT");
          break;
        case "udp":
          args.push("-sU");
          break;
        case "comprehensive":
          args.push("-sS", "-sU", "-sV", "-O");
          break;
        case "fast":
          args.push("-F");
          break;
        case "stealth":
          args.push("-sS", "-T2");
          break;
        default:
          // Utiliser le type par défaut
          break;
      }
    }

    // Intensité du scan
    if (options.intensity !== undefined) {
      const intensity = parseInt(options.intensity, 10);
      if (intensity >= 0 && intensity <= 5) {
        args.push(`-T${intensity}`);
      }
    }

    // Ports spécifiques
    if (options.ports) {
      args.push("-p", options.ports);
    }

    // Détection de version
    if (options.detectVersions) {
      args.push("-sV");
    }

    // Détection du système d'exploitation
    if (options.detectOS) {
      args.push("-O");
    }

    // Scripts NSE
    if (options.scripts) {
      if (Array.isArray(options.scripts)) {
        args.push("--script", options.scripts.join(","));
      } else if (typeof options.scripts === "string") {
        args.push("--script", options.scripts);
      }
    }

    // Format de sortie XML pour analyse
    args.push("-oX", "-");

    // Assembler la commande complète (pour affichage)
    const command = `nmap ${args.join(" ")} ${targets.join(" ")}`;

    return {
      targets,
      args,
      command,
    };
  }

  /**
   * Exécute un scan Nmap
   * @param {Array} targets - Cibles du scan
   * @param {Array} args - Arguments Nmap
   * @returns {Promise<string>} Résultats du scan en XML
   * @private
   */
  async _executeScan(targets, args) {
    return new Promise((resolve, reject) => {
      console.log(
        `[NmapAgent] Exécution de Nmap avec les arguments: ${args.join(" ")}`
      );

      // Dans une implémentation réelle, il faudrait vérifier que Nmap est installé
      // et exécuter la commande. Pour cet exemple, nous simulons le résultat.

      // Simulation d'un scan Nmap (pour les besoins de l'exemple)
      setTimeout(() => {
        const simulatedXml = this._generateSimulatedResult(targets);
        resolve(simulatedXml);
      }, 2000);

      // Exemple d'exécution réelle (commenté pour l'exemple)
      /*
      const nmapProcess = spawn('nmap', [...args, ...targets]);
      
      let stdout = '';
      let stderr = '';
      
      nmapProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      nmapProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      nmapProcess.on('error', (error) => {
        reject(new Error(`Erreur d'exécution Nmap: ${error.message}`));
      });
      
      nmapProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Nmap a retourné un code d'erreur ${code}: ${stderr}`));
          return;
        }
        
        resolve(stdout);
      });
      
      // Définir un timeout
      const timeout = setTimeout(() => {
        nmapProcess.kill();
        reject(new Error(`Timeout du scan après ${this.config.timeoutSeconds} secondes`));
      }, this.config.timeoutSeconds * 1000);
      
      // Nettoyer le timeout à la fin
      nmapProcess.on('close', () => clearTimeout(timeout));
      */
    });
  }

  /**
   * Génère un résultat simulé pour l'exemple
   * @param {Array} targets - Cibles du scan
   * @returns {string} Résultat XML simulé
   * @private
   */
  _generateSimulatedResult(targets) {
    // Créer un résultat XML simulé pour chaque cible
    const hostResults = targets.map((target) => {
      const ipMatch = target.match(/\b(?:\d{1,3}\.){3}\d{1,3}\b/);
      const ip = ipMatch ? ipMatch[0] : "192.168.1.1";

      // Générer des ports aléatoires
      const ports = [];
      const numPorts = Math.floor(Math.random() * 5) + 1;
      const commonPorts = [22, 80, 443, 25, 21, 3306, 8080, 8443];

      for (let i = 0; i < numPorts; i++) {
        const portNum =
          commonPorts[Math.floor(Math.random() * commonPorts.length)];
        const state = Math.random() > 0.3 ? "open" : "closed";
        const service = this._getServiceForPort(portNum);

        ports.push(
          `<port protocol="tcp" portid="${portNum}"><state state="${state}" reason="syn-ack" reason_ttl="64"/><service name="${service.name}" product="${service.product}" version="${service.version}" method="probed" conf="10"/></port>`
        );
      }

      return `
        <host>
          <status state="up" reason="echo-reply" reason_ttl="64"/>
          <address addr="${ip}" addrtype="ipv4"/>
          <hostnames>
            <hostname name="host-${ip.replace(/\./g, "-")}.local" type="PTR"/>
          </hostnames>
          <ports>
            ${ports.join("\n")}
          </ports>
          <os>
            <osmatch name="Linux 4.15 - 5.6" accuracy="95" line="67241">
              <osclass type="general purpose" vendor="Linux" osfamily="Linux" osgen="4.X" accuracy="95"/>
            </osmatch>
          </os>
        </host>
      `;
    });

    // Créer le document XML complet
    return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap ${targets.join(" ")}" start="${Math.floor(
      Date.now() / 1000
    )}" startstr="${new Date().toISOString()}" version="7.91" xmloutputversion="1.05">
  <scaninfo type="syn" protocol="tcp" numservices="1000" services="1,3-4,..."/>
  <verbose level="0"/>
  <debugging level="0"/>
  ${hostResults.join("\n")}
  <runstats>
    <finished time="${Math.floor(
      Date.now() / 1000
    )}" timestr="${new Date().toISOString()}" elapsed="2.05" summary="Nmap done at ${new Date().toISOString()}; ${
      targets.length
    } IP address (${
      targets.length
    } host up) scanned in 2.05 seconds" exit="success"/>
    <hosts up="${targets.length}" down="0" total="${targets.length}"/>
  </runstats>
</nmaprun>`;
  }

  /**
   * Obtient un service pour un port donné
   * @param {number} port - Numéro de port
   * @returns {Object} Informations sur le service
   * @private
   */
  _getServiceForPort(port) {
    const services = {
      22: { name: "ssh", product: "OpenSSH", version: "8.2p1 Ubuntu" },
      80: { name: "http", product: "Apache httpd", version: "2.4.41" },
      443: { name: "https", product: "nginx", version: "1.18.0" },
      25: { name: "smtp", product: "Postfix smtpd", version: "" },
      21: { name: "ftp", product: "vsftpd", version: "3.0.3" },
      3306: { name: "mysql", product: "MySQL", version: "8.0.30" },
      8080: { name: "http-proxy", product: "Apache Tomcat", version: "9.0.46" },
      8443: { name: "https-alt", product: "Apache Tomcat", version: "9.0.46" },
    };

    return services[port] || { name: "unknown", product: "", version: "" };
  }

  /**
   * Analyse les résultats XML de Nmap
   * @param {string} xmlResults - Résultats XML de Nmap
   * @returns {Object} Résultats analysés
   * @private
   */
  _parseResults(xmlResults) {
    // Dans une implémentation réelle, on utiliserait une bibliothèque XML
    // comme xml2js pour parser correctement les résultats.
    // Pour cet exemple, nous allons simuler le parsing.

    console.log(
      `[NmapAgent] Analyse des résultats XML (${xmlResults.length} caractères)`
    );

    // Analyse du nombre d'hôtes
    const hostUpMatch = xmlResults.match(/<hosts up="(\d+)"/);
    const hostsUp = hostUpMatch ? parseInt(hostUpMatch[1], 10) : 0;

    // Analyse des hôtes individuels
    const hostBlocks = xmlResults.match(/<host>[\s\S]*?<\/host>/g) || [];

    // Informations de synthèse
    const summary = {
      hostsScanned: hostBlocks.length,
      hostsUp: hostsUp,
      totalPorts: 0,
      openPorts: 0,
      startTime: new Date().toISOString(),
      endTime: new Date().toISOString(),
      scanDuration: 0,
    };

    // Extraire les informations de chaque hôte
    const hosts = hostBlocks.map((hostBlock) => {
      // Extraire l'adresse IP
      const ipMatch = hostBlock.match(
        /<address addr="([^"]+)" addrtype="ipv4"/
      );
      const ip = ipMatch ? ipMatch[1] : "unknown";

      // Extraire le nom d'hôte
      const hostnameMatch = hostBlock.match(/<hostname name="([^"]+)"/);
      const hostname = hostnameMatch ? hostnameMatch[1] : "";

      // Extraire les informations de système d'exploitation
      const osMatch = hostBlock.match(
        /<osmatch name="([^"]+)" accuracy="([^"]+)"/
      );
      const os = osMatch
        ? {
            name: osMatch[1],
            accuracy: parseInt(osMatch[2], 10),
          }
        : { name: "Unknown", accuracy: 0 };

      // Extraire les ports
      const portBlocks = hostBlock.match(/<port[\s\S]*?<\/port>/g) || [];

      const ports = portBlocks.map((portBlock) => {
        const portIdMatch = portBlock.match(/portid="(\d+)"/);
        const protocolMatch = portBlock.match(/protocol="([^"]+)"/);
        const stateMatch = portBlock.match(/<state state="([^"]+)"/);
        const serviceNameMatch = portBlock.match(/<service name="([^"]+)"/);
        const productMatch = portBlock.match(/product="([^"]+)"/);
        const versionMatch = portBlock.match(/version="([^"]+)"/);

        return {
          port: portIdMatch ? parseInt(portIdMatch[1], 10) : 0,
          protocol: protocolMatch ? protocolMatch[1] : "tcp",
          state: stateMatch ? stateMatch[1] : "unknown",
          service: {
            name: serviceNameMatch ? serviceNameMatch[1] : "unknown",
            product: productMatch ? productMatch[1] : "",
            version: versionMatch ? versionMatch[1] : "",
          },
        };
      });

      // Mettre à jour les statistiques
      summary.totalPorts += ports.length;
      summary.openPorts += ports.filter((p) => p.state === "open").length;

      return {
        ip,
        hostname,
        os,
        ports,
        status: "up",
      };
    });

    return {
      summary,
      hosts,
    };
  }

  /**
   * Génère un rapport à partir des résultats analysés
   * @param {Object} results - Résultats analysés
   * @param {Object} command - Informations sur la commande exécutée
   * @param {number} scanTime - Temps d'exécution du scan en ms
   * @returns {string} Rapport formaté
   * @private
   */
  _generateReport(results, command, scanTime) {
    const { summary, hosts } = results;

    // Formatage de la durée du scan
    const duration =
      scanTime > 1000
        ? `${(scanTime / 1000).toFixed(2)} secondes`
        : `${scanTime} ms`;

    // Construire le rapport
    let report = `# Rapport de scan réseau Nmap\n\n`;
    report += `## Résumé\n\n`;
    report += `- **Date**: ${new Date().toISOString()}\n`;
    report += `- **Cibles**: ${command.targets.join(", ")}\n`;
    report += `- **Commande**: ${command.command}\n`;
    report += `- **Durée**: ${duration}\n`;
    report += `- **Hôtes analysés**: ${summary.hostsScanned}\n`;
    report += `- **Hôtes actifs**: ${summary.hostsUp}\n`;
    report += `- **Ports totaux analysés**: ${summary.totalPorts}\n`;
    report += `- **Ports ouverts trouvés**: ${summary.openPorts}\n\n`;

    report += `## Détails par hôte\n\n`;

    // Informations pour chaque hôte
    hosts.forEach((host) => {
      report += `### Hôte: ${host.ip}\n\n`;

      if (host.hostname) {
        report += `- **Nom d'hôte**: ${host.hostname}\n`;
      }

      report += `- **Système d'exploitation**: ${host.os.name} (précision: ${host.os.accuracy}%)\n`;
      report += `- **État**: ${host.status}\n\n`;

      if (host.ports.length > 0) {
        report += `#### Ports\n\n`;
        report += `| Port | Protocole | État | Service | Produit | Version |\n`;
        report += `|------|-----------|------|---------|---------|--------|\n`;

        host.ports.forEach((port) => {
          report += `| ${port.port} | ${port.protocol} | ${port.state} | ${port.service.name} | ${port.service.product} | ${port.service.version} |\n`;
        });

        report += `\n`;
      } else {
        report += `Aucun port détecté pour cet hôte.\n\n`;
      }
    });

    report += `## Recommandations de sécurité\n\n`;

    // Générer des recommandations basées sur les résultats
    const openPorts = hosts.flatMap((host) =>
      host.ports
        .filter((port) => port.state === "open")
        .map((port) => ({ host: host.ip, ...port }))
    );

    if (openPorts.length > 0) {
      report += `Les ports ouverts suivants ont été détectés et pourraient présenter des risques de sécurité :\n\n`;

      // Rechercher des services potentiellement vulnérables
      const commonVulnerableServices = [
        {
          port: 21,
          service: "ftp",
          recommendation:
            "Envisagez de désactiver FTP et d'utiliser SFTP (SSH) à la place.",
        },
        {
          port: 23,
          service: "telnet",
          recommendation:
            "Telnet transmet les données en clair. Utilisez SSH à la place.",
        },
        {
          port: 25,
          service: "smtp",
          recommendation:
            "Assurez-vous que votre serveur SMTP est correctement configuré et n'est pas un relais ouvert.",
        },
        {
          port: 3306,
          service: "mysql",
          recommendation:
            "Limitez l'accès à MySQL depuis l'extérieur de votre réseau.",
        },
        {
          port: 5432,
          service: "postgresql",
          recommendation:
            "Limitez l'accès à PostgreSQL depuis l'extérieur de votre réseau.",
        },
        {
          port: 8080,
          service: "http-proxy",
          recommendation:
            "Protégez ce service proxy ou utilisez HTTPS (8443) à la place.",
        },
      ];

      // Ajouter des recommandations spécifiques
      commonVulnerableServices.forEach((vulnService) => {
        const matchingPorts = openPorts.filter(
          (p) =>
            p.port === vulnService.port ||
            p.service.name === vulnService.service
        );

        if (matchingPorts.length > 0) {
          const hosts = matchingPorts.map((p) => p.host).join(", ");
          report += `- **${vulnService.service.toUpperCase()} (Port ${
            vulnService.port
          })**: Détecté sur ${hosts}. ${vulnService.recommendation}\n`;
        }
      });

      // Recommandations générales
      report += `\n### Recommandations générales\n\n`;
      report += `1. **Principe du moindre privilège**: Fermez tous les ports qui ne sont pas nécessaires.\n`;
      report += `2. **Maintenir à jour**: Assurez-vous que tous les services sont à jour pour éviter les vulnérabilités connues.\n`;
      report += `3. **Pare-feu**: Configurez votre pare-feu pour limiter l'accès aux services essentiels uniquement.\n`;
      report += `4. **Authentification forte**: Utilisez des mots de passe forts et l'authentification à deux facteurs lorsque c'est possible.\n`;
    } else {
      report += `Aucun port ouvert n'a été détecté. Continuez à surveiller régulièrement votre réseau pour détecter toute modification.\n`;
    }

    return report;
  }

  /**
   * Récupère les métadonnées de l'agent
   * @returns {Object} Métadonnées
   */
  get_metadata() {
    return {
      id: this.id,
      name: this.name,
      description: this.description,
      capabilities: this.capabilities,
      agent_type: this.agent_type,
      category: this.category,
      active: this.active,
      statistics: {
        ...this.statistics,
        uptime: process.uptime(),
      },
    };
  }
}

// Exporter l'agent
module.exports = NmapAgent;

const BaseOSINTAgent = require('../../core/BaseOSINTAgent');
const dns = require('dns').promises;
const whois = require('whois-json');
const axios = require('axios');

class DomainInvestigator extends BaseOSINTAgent {
    constructor(config = {}) {
        super(config);
        this.name = 'DomainInvestigator';
    }

    async _investigate(target) {
        if (!target.domain) {
            throw new Error('Domain is required for investigation');
        }

        const domain = target.domain.toLowerCase();
        const results = {
            domain,
            timestamp: new Date().toISOString(),
            dns: {},
            whois: {},
            security: {},
            technologies: {}
        };

        // DNS Records
        try {
            results.dns = await this._gatherDNSInfo(domain);
        } catch (error) {
            this.emit('warning', { type: 'dns', error: error.message });
        }

        // WHOIS Information
        try {
            results.whois = await this._gatherWHOISInfo(domain);
        } catch (error) {
            this.emit('warning', { type: 'whois', error: error.message });
        }

        // Security Information
        try {
            results.security = await this._gatherSecurityInfo(domain);
        } catch (error) {
            this.emit('warning', { type: 'security', error: error.message });
        }

        // Technology Stack
        try {
            results.technologies = await this._gatherTechnologyInfo(domain);
        } catch (error) {
            this.emit('warning', { type: 'technologies', error: error.message });
        }

        return results;
    }

    async _gatherDNSInfo(domain) {
        const dnsInfo = {};
        
        // A Records
        try {
            dnsInfo.a = await dns.resolve(domain, 'A');
        } catch (error) {
            dnsInfo.a = [];
        }

        // MX Records
        try {
            dnsInfo.mx = await dns.resolve(domain, 'MX');
        } catch (error) {
            dnsInfo.mx = [];
        }

        // NS Records
        try {
            dnsInfo.ns = await dns.resolve(domain, 'NS');
        } catch (error) {
            dnsInfo.ns = [];
        }

        // TXT Records
        try {
            dnsInfo.txt = await dns.resolve(domain, 'TXT');
        } catch (error) {
            dnsInfo.txt = [];
        }

        return dnsInfo;
    }

    async _gatherWHOISInfo(domain) {
        return await whois(domain);
    }

    async _gatherSecurityInfo(domain) {
        const securityInfo = {};

        // SSL/TLS Information
        try {
            const response = await axios.get(`https://${domain}`, {
                validateStatus: () => true
            });
            securityInfo.ssl = {
                valid: response.request.res.socket.authorized,
                protocol: response.request.res.socket.getProtocol(),
                cipher: response.request.res.socket.getCipher()
            };
        } catch (error) {
            securityInfo.ssl = { error: error.message };
        }

        // Security Headers
        try {
            const response = await axios.get(`https://${domain}`, {
                validateStatus: () => true
            });
            securityInfo.headers = response.headers;
        } catch (error) {
            securityInfo.headers = { error: error.message };
        }

        return securityInfo;
    }

    async _gatherTechnologyInfo(domain) {
        // This would typically integrate with services like BuiltWith or Wappalyzer
        // For now, returning a placeholder
        return {
            message: 'Technology detection requires integration with external services'
        };
    }

    async _generateMarkdownReport(results) {
        return `# Domain Investigation Report: ${results.domain}

## Investigation Details
- **Timestamp**: ${results.timestamp}
- **Status**: ${this.status}

## DNS Information
${this._formatDNSInfo(results.dns)}

## WHOIS Information
${this._formatWHOISInfo(results.whois)}

## Security Information
${this._formatSecurityInfo(results.security)}

## Technology Stack
${this._formatTechnologyInfo(results.technologies)}
`;
    }

    _formatDNSInfo(dnsInfo) {
        return `
### A Records
${dnsInfo.a.join('\n')}

### MX Records
${dnsInfo.mx.map(mx => `${mx.exchange} (Priority: ${mx.priority})`).join('\n')}

### NS Records
${dnsInfo.ns.join('\n')}

### TXT Records
${dnsInfo.txt.join('\n')}
`;
    }

    _formatWHOISInfo(whoisInfo) {
        return `
### Registrar
- **Name**: ${whoisInfo.registrar || 'N/A'}
- **Registration Date**: ${whoisInfo.creationDate || 'N/A'}
- **Expiration Date**: ${whoisInfo.expirationDate || 'N/A'}

### Contact Information
- **Registrant**: ${whoisInfo.registrant || 'N/A'}
- **Admin Contact**: ${whoisInfo.adminContact || 'N/A'}
- **Technical Contact**: ${whoisInfo.technicalContact || 'N/A'}
`;
    }

    _formatSecurityInfo(securityInfo) {
        return `
### SSL/TLS Information
- **Valid**: ${securityInfo.ssl.valid ? 'Yes' : 'No'}
- **Protocol**: ${securityInfo.ssl.protocol || 'N/A'}
- **Cipher**: ${securityInfo.ssl.cipher ? securityInfo.ssl.cipher.name : 'N/A'}

### Security Headers
${Object.entries(securityInfo.headers || {})
    .map(([key, value]) => `- **${key}**: ${value}`)
    .join('\n')}
`;
    }

    _formatTechnologyInfo(techInfo) {
        return `
${techInfo.message}
`;
    }

    async _generateMaltegoTransform(results) {
        // This would generate Maltego transform data
        // For now, returning a placeholder
        return {
            message: 'Maltego transform generation requires integration with Maltego API'
        };
    }
}

module.exports = DomainInvestigator; 
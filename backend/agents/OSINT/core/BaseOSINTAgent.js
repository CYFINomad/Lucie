const { EventEmitter } = require('events');

class BaseOSINTAgent extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = config;
        this.results = new Map();
        this.status = 'idle';
        this.startTime = null;
        this.endTime = null;
    }

    /**
     * Initialize the agent with configuration
     * @param {Object} config - Configuration object
     */
    async initialize(config = {}) {
        this.config = { ...this.config, ...config };
        this.status = 'initialized';
        this.emit('initialized', this.config);
    }

    /**
     * Start the investigation
     * @param {Object} target - Target to investigate
     */
    async investigate(target) {
        this.startTime = new Date();
        this.status = 'running';
        this.emit('started', { target, startTime: this.startTime });

        try {
            const results = await this._investigate(target);
            this.results.set(target, results);
            this.status = 'completed';
            this.endTime = new Date();
            this.emit('completed', { target, results, endTime: this.endTime });
            return results;
        } catch (error) {
            this.status = 'error';
            this.emit('error', { target, error });
            throw error;
        }
    }

    /**
     * Abstract method to be implemented by specific agents
     * @param {Object} target - Target to investigate
     */
    async _investigate(target) {
        throw new Error('_investigate method must be implemented by specific agent');
    }

    /**
     * Generate a markdown report
     * @param {Object} target - Target to generate report for
     */
    async generateMarkdownReport(target) {
        const results = this.results.get(target);
        if (!results) {
            throw new Error('No results available for target');
        }
        return this._generateMarkdownReport(results);
    }

    /**
     * Generate Maltego transform data
     * @param {Object} target - Target to generate transform for
     */
    async generateMaltegoTransform(target) {
        const results = this.results.get(target);
        if (!results) {
            throw new Error('No results available for target');
        }
        return this._generateMaltegoTransform(results);
    }

    /**
     * Export results in specified format
     * @param {Object} target - Target to export
     * @param {string} format - Export format (json, markdown, maltego)
     */
    async exportResults(target, format = 'json') {
        const results = this.results.get(target);
        if (!results) {
            throw new Error('No results available for target');
        }

        switch (format.toLowerCase()) {
            case 'json':
                return JSON.stringify(results, null, 2);
            case 'markdown':
                return this.generateMarkdownReport(target);
            case 'maltego':
                return this.generateMaltegoTransform(target);
            default:
                throw new Error(`Unsupported export format: ${format}`);
        }
    }

    /**
     * Get agent status
     */
    getStatus() {
        return {
            status: this.status,
            startTime: this.startTime,
            endTime: this.endTime,
            resultsCount: this.results.size
        };
    }

    /**
     * Clear results for a specific target
     * @param {Object} target - Target to clear results for
     */
    clearResults(target) {
        this.results.delete(target);
    }

    /**
     * Clear all results
     */
    clearAllResults() {
        this.results.clear();
    }
}

module.exports = BaseOSINTAgent; 
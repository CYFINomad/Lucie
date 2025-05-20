const BaseOSINTAgent = require('../../core/BaseOSINTAgent');
const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

class TranslationAgent extends BaseOSINTAgent {
    constructor(config = {}) {
        super(config);
        this.name = 'TranslationAgent';
        this.learningDataPath = path.join(__dirname, '../../../data/translation_learning.json');
        this.supportedLanguages = [
            'BG', 'CS', 'DA', 'DE', 'EL', 'EN', 'ES', 'ET', 'FI', 'FR', 'HU', 'ID', 'IT', 'JA', 'KO',
            'LT', 'LV', 'NB', 'NL', 'PL', 'PT', 'RO', 'RU', 'SK', 'SL', 'SV', 'TR', 'UK', 'ZH'
        ];
    }

    async initialize(config = {}) {
        await super.initialize(config);
        
        // Ensure DeepL API key is provided
        if (!this.config.deeplApiKey) {
            throw new Error('DeepL API key is required');
        }

        // Initialize learning data
        await this._initializeLearningData();
    }

    async _investigate(target) {
        if (!target.text || !target.targetLanguage) {
            throw new Error('Text and target language are required for translation');
        }

        const results = {
            originalText: target.text,
            originalLanguage: target.sourceLanguage || await this._detectLanguage(target.text),
            targetLanguage: target.targetLanguage,
            timestamp: new Date().toISOString(),
            translations: {},
            learningData: {}
        };

        // Perform translation
        try {
            results.translations = await this._translateText(
                target.text,
                target.sourceLanguage,
                target.targetLanguage
            );
        } catch (error) {
            this.emit('warning', { type: 'translation', error: error.message });
        }

        // Update learning data
        try {
            results.learningData = await this._updateLearningData(results);
        } catch (error) {
            this.emit('warning', { type: 'learning', error: error.message });
        }

        return results;
    }

    async _translateText(text, sourceLanguage, targetLanguage) {
        const url = 'https://api-free.deepl.com/v2/translate';
        const params = {
            auth_key: this.config.deeplApiKey,
            text: text,
            target_lang: targetLanguage
        };

        if (sourceLanguage) {
            params.source_lang = sourceLanguage;
        }

        try {
            const response = await axios.post(url, null, { params });
            return {
                translatedText: response.data.translations[0].text,
                detectedLanguage: response.data.translations[0].detected_source_language,
                confidence: response.data.translations[0].confidence || 1.0
            };
        } catch (error) {
            throw new Error(`Translation failed: ${error.message}`);
        }
    }

    async _detectLanguage(text) {
        const url = 'https://api-free.deepl.com/v2/detect';
        const params = {
            auth_key: this.config.deeplApiKey,
            text: text
        };

        try {
            const response = await axios.post(url, null, { params });
            return response.data[0].language;
        } catch (error) {
            throw new Error(`Language detection failed: ${error.message}`);
        }
    }

    async _initializeLearningData() {
        try {
            await fs.access(this.learningDataPath);
        } catch {
            // Create learning data file if it doesn't exist
            await fs.writeFile(this.learningDataPath, JSON.stringify({
                translations: {},
                languagePairs: {},
                confidenceScores: {}
            }, null, 2));
        }
    }

    async _updateLearningData(results) {
        const learningData = JSON.parse(await fs.readFile(this.learningDataPath, 'utf8'));
        const { originalText, originalLanguage, targetLanguage, translations } = results;

        // Update translations database
        const translationKey = `${originalLanguage}-${targetLanguage}`;
        if (!learningData.translations[translationKey]) {
            learningData.translations[translationKey] = [];
        }
        learningData.translations[translationKey].push({
            original: originalText,
            translated: translations.translatedText,
            confidence: translations.confidence,
            timestamp: results.timestamp
        });

        // Update language pair statistics
        if (!learningData.languagePairs[translationKey]) {
            learningData.languagePairs[translationKey] = {
                count: 0,
                averageConfidence: 0
            };
        }
        const pair = learningData.languagePairs[translationKey];
        pair.count++;
        pair.averageConfidence = (pair.averageConfidence * (pair.count - 1) + translations.confidence) / pair.count;

        // Save updated learning data
        await fs.writeFile(this.learningDataPath, JSON.stringify(learningData, null, 2));

        return {
            translationKey,
            pairStatistics: pair
        };
    }

    async _generateMarkdownReport(results) {
        return `# Translation Report

## Translation Details
- **Original Text**: ${results.originalText}
- **Original Language**: ${results.originalLanguage}
- **Target Language**: ${results.targetLanguage}
- **Timestamp**: ${results.timestamp}

## Translation Results
- **Translated Text**: ${results.translations.translatedText}
- **Detected Language**: ${results.translations.detectedLanguage}
- **Confidence**: ${(results.translations.confidence * 100).toFixed(2)}%

## Learning Data
- **Translation Key**: ${results.learningData.translationKey}
- **Total Translations**: ${results.learningData.pairStatistics.count}
- **Average Confidence**: ${(results.learningData.pairStatistics.averageConfidence * 100).toFixed(2)}%
`;
    }

    async _generateMaltegoTransform(results) {
        return {
            entities: [
                {
                    type: 'lucie.Translation',
                    value: results.originalText,
                    properties: {
                        originalLanguage: results.originalLanguage,
                        targetLanguage: results.targetLanguage,
                        translatedText: results.translations.translatedText,
                        confidence: results.translations.confidence
                    }
                }
            ]
        };
    }

    /**
     * Get supported languages
     */
    getSupportedLanguages() {
        return this.supportedLanguages;
    }

    /**
     * Get learning statistics for a specific language pair
     * @param {string} sourceLanguage - Source language code
     * @param {string} targetLanguage - Target language code
     */
    async getLearningStatistics(sourceLanguage, targetLanguage) {
        const learningData = JSON.parse(await fs.readFile(this.learningDataPath, 'utf8'));
        const translationKey = `${sourceLanguage}-${targetLanguage}`;
        return learningData.languagePairs[translationKey] || null;
    }
}

module.exports = TranslationAgent; 
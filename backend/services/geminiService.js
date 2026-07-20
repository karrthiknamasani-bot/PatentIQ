const { GoogleGenAI } = require('@google/genai');
const promptBuilder = require('./promptBuilder');

class GeminiService {
  constructor() {
    this.modelName = 'gemini-3.1-flash-lite';
  }

  get ai() {
    if (!this._ai) {
      this._ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    }
    return this._ai;
  }

  /**
   * Cleans potential markdown formatting from the response
   * @param {string} text 
   * @returns {string}
   */
  _cleanJson(text) {
    let clean = text.trim();
    if (clean.startsWith('```json')) {
      clean = clean.replace(/^```json/, '');
    }
    if (clean.startsWith('```')) {
      clean = clean.replace(/^```/, '');
    }
    if (clean.endsWith('```')) {
      clean = clean.replace(/```$/, '');
    }
    return clean.trim();
  }

  /**
   * Generates a structured JSON analysis using Gemini 2.5 Flash
   * @param {string} projectTitle 
   * @param {string} projectFullText 
   * @param {Array} retrievedPatents 
   * @returns {Object} Parsed JSON object
   */
  async generateStructuredAnalysis(projectTitle, projectFullText, retrievedPatents) {
    const prompt = promptBuilder.buildAnalysisPrompt(projectTitle, projectFullText, retrievedPatents);
    
    let attempt = 1;
    const maxAttempts = 2; // Retry once if invalid JSON

    while (attempt <= maxAttempts) {
      try {
        console.log(`[GeminiService] Calling ${this.modelName} (Attempt ${attempt})...`);
        const response = await this.ai.models.generateContent({
          model: this.modelName,
          contents: prompt,
          config: {
            temperature: 0.1,
            responseMimeType: 'application/json',
          }
        });

        if (!response || !response.text) {
          throw new Error("Empty response received from Gemini API");
        }

        console.log(`[GeminiService] Response received.`);
        const cleanText = this._cleanJson(response.text);
        
        console.log(`[GeminiService] Parsing JSON...`);
        const parsedJson = JSON.parse(cleanText);
        
        return parsedJson;

      } catch (error) {
        console.error(`[GeminiService] Attempt ${attempt} failed: ${error.message}`);
        if (attempt === maxAttempts) {
          throw new Error(`Failed to generate valid JSON analysis after ${maxAttempts} attempts. Last error: ${error.message}`);
        }
        attempt++;
      }
    }
  }
}

module.exports = new GeminiService();

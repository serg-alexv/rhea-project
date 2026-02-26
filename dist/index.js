"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.tribunalFlow = exports.ai = void 0;
const genkit_1 = require("genkit");
const googleai_1 = require("@genkit-ai/googleai");
const firebase_1 = require("@genkit-ai/firebase");
(0, firebase_1.enableFirebaseTelemetry)();
exports.ai = (0, genkit_1.genkit)({
    plugins: [(0, googleai_1.googleAI)()],
    model: googleai_1.gemini15Flash,
});
exports.tribunalFlow = exports.ai.defineFlow('tribunalFlow', async (hypothesis) => {
    const { text } = await exports.ai.generate({
        prompt: `Analyze this hypothesis for scientific isomorphism: ${hypothesis}`,
        config: { temperature: 0.2 }
    });
    return text;
});
// Start the Genkit server
exports.ai.startFlowServer();

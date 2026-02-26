import { genkit } from 'genkit';
import { googleAI, gemini15Flash } from '@genkit-ai/googleai';
import { enableFirebaseTelemetry } from '@genkit-ai/firebase';

// Enable AI Monitoring and Tracing
enableFirebaseTelemetry();

export const ai = genkit({
  plugins: [googleAI()],
  model: gemini15Flash,
});

export const tribunalFlow = ai.defineFlow('tribunalFlow', async (hypothesis) => {
  const { text } = await ai.generate({
    prompt: `Analyze this hypothesis for scientific isomorphism: ${hypothesis}`,
    config: { temperature: 0.2 }
  });
  return text;
});

// Cloud Run requires listening on the port defined by the PORT env var
const port = process.env.PORT ? parseInt(process.env.PORT) : 8080;
ai.startFlowServer({ port });

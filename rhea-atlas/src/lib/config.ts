/**
 * Environment-aware API configuration for Orion Atlas.
 * Set NEXT_PUBLIC_RHEA_API and NEXT_PUBLIC_TRIBUNAL_API in your deployment
 * environment (Vercel env vars, .env.local, etc.) to point at the real backend.
 */

export const API_BASE: string =
  process.env.NEXT_PUBLIC_RHEA_API ?? 'http://localhost:8000';

export const TRIBUNAL_API: string =
  process.env.NEXT_PUBLIC_TRIBUNAL_API ?? `${API_BASE}/api`;

export const IS_PRODUCTION: boolean = process.env.NODE_ENV === 'production';

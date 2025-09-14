#!/usr/bin/env node

/**
 * Node.js polyfill for Cloudflare Workers imports
 * This script sets up a module resolution hook to handle cloudflare: protocol imports
 */

import { createRequire } from 'module';

// Simple DurableObject polyfill
class DurableObject {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }
}

// Simple polyfill for cloudflare:workers
const cloudflareWorkersPolyfill = {
  DurableObject,
  WorkerEntrypoint: class WorkerEntrypoint {
    constructor(ctx, env) {
      this.ctx = ctx;
      this.env = env;
    }

    fetch(request, env, ctx) {
      throw new Error('fetch method must be implemented');
    }
  }
};

// Export the polyfills
export { DurableObject, cloudflareWorkersPolyfill };
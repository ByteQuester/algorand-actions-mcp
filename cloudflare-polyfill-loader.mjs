// Custom ESM loader that polyfills cloudflare: imports
export async function resolve(specifier, context, defaultResolve) {
  // Handle cloudflare: protocol imports
  if (specifier.startsWith('cloudflare:')) {
    // Return a data URL with our polyfill
    if (specifier === 'cloudflare:workers') {
      return {
        url: 'data:application/javascript,export class DurableObject { constructor(state, env) { this.state = state; this.env = env; } } export class WorkerEntrypoint { constructor(ctx, env) { this.ctx = ctx; this.env = env; } fetch() { throw new Error("fetch method must be implemented"); } }',
        format: 'module',
        shortCircuit: true
      };
    }
  }

  // For all other imports, use the default resolver
  return defaultResolve(specifier, context);
}

export async function load(url, context, defaultLoad) {
  return defaultLoad(url, context);
}
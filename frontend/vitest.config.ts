/// <reference types="vitest" />
import { defineConfig } from 'vite';

export default defineConfig({
    resolve: {
        conditions: ['development', 'browser'],
    },
    // @ts-ignore - vitest config
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['./src/setupTests.ts'],
    },
});

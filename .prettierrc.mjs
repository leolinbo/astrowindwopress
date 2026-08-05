/** @type {import('prettier').Config} */
export default {
  printWidth: 120,
  semi: true,
  singleQuote: true,
  tabWidth: 2,
  trailingComma: 'es5',
  useTabs: false,
  endOfLine: 'auto',

  plugins: ['prettier-plugin-astro'],

  overrides: [{ files: '*.astro', options: { parser: 'astro' } }],
};

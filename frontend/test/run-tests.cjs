const path = require('path');
const { spawnSync } = require('child_process');
const preload = path.join(__dirname, 'disable-native-canvas.cjs').replace(/\\/g, '/');
const result = spawnSync(process.execPath, [require.resolve('@craco/craco/dist/bin/craco.js'), 'test', ...process.argv.slice(2)], {
  stdio: 'inherit',
  env: { ...process.env, NODE_OPTIONS: `${process.env.NODE_OPTIONS || ''} --require="${preload}"`.trim() },
});
if (result.error) throw result.error;
process.exit(result.status ?? 1);

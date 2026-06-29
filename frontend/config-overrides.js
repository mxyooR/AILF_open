const path = require('path');
const webpack = require('webpack');

module.exports = function override(config, env) {
  // 添加 fallback 配置以解决一些依赖问题
  config.resolve.fallback = {
    ...config.resolve.fallback,
    "path": require.resolve("path-browserify"),
    "os": require.resolve("os-browserify/browser"),
    "crypto": require.resolve("crypto-browserify"),
    "stream": require.resolve("stream-browserify"),
    "buffer": require.resolve("buffer"),
    "process": require.resolve("process/browser"),
  };

  // 添加 alias 配置
  config.resolve.alias = {
    ...config.resolve.alias,
    '@': path.resolve(__dirname, 'src'),
    // 彻底忽略 react-pdf 包
    'react-pdf': false,
  };

  // 修复 ES 模块解析问题
  config.module.rules.unshift({
    test: /\.m?js$/,
    type: 'javascript/auto',
    resolve: {
      fullySpecified: false,
    },
  });

  // 修复 react-pdf 等第三方库的 jsx-runtime 解析问题
  config.resolve.extensionAlias = {
    ...config.resolve.extensionAlias,
    '.js': ['.js', '.jsx', '.ts', '.tsx'],
  };

  // 使用 IgnorePlugin 彻底忽略 react-pdf
  config.plugins = config.plugins || [];
  config.plugins.push(
    new webpack.IgnorePlugin({
      resourceRegExp: /^react-pdf$/,
    })
  );

  return config;
};

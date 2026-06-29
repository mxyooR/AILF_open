const path = require('path');
const webpack = require('webpack');

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Add fallback configurations for Node.js core modules
      webpackConfig.resolve.fallback = {
        ...webpackConfig.resolve.fallback,
        "path": require.resolve("path-browserify"),
        "os": require.resolve("os-browserify/browser"),
        "crypto": require.resolve("crypto-browserify"),
        "stream": require.resolve("stream-browserify"),
        "buffer": require.resolve("buffer"),
        "process": require.resolve("process/browser"),
      };

      // Add alias for resolving '@' to 'src'
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        '@': path.resolve(__dirname, 'src'),
      };

      // Ensure the new JSX transform is used
      // This is often the fix for 'react/jsx-runtime' errors
      const babelLoader = webpackConfig.module.rules.find(
        (rule) =>
          rule.oneOf &&
          rule.oneOf.find(
            (oneOfRule) =>
              oneOfRule.loader && oneOfRule.loader.includes('babel-loader')
          )
      );

      if (babelLoader) {
        const babelLoaderConfig = babelLoader.oneOf.find(
          (oneOfRule) =>
            oneOfRule.loader && oneOfRule.loader.includes('babel-loader')
        );
        if (babelLoaderConfig) {
          babelLoaderConfig.options.presets = (babelLoaderConfig.options.presets || []).map(preset => {
            if (preset.includes('babel-preset-react-app')) {
              return [preset, { runtime: 'automatic' }];
            }
            return preset;
          });
        }
      }

      // The rule for .m?js files might still be needed for other ESM issues
      webpackConfig.module.rules.push({
        test: /\.m?js$/,
        resolve: {
          fullySpecified: false,
        },
      });

      return webpackConfig;
    },
  },
  devServer: {
    port: 3000,
    open: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
      },
    },
    client: {
      // 禁用错误覆盖层，避免ResizeObserver等无害错误弹窗
      overlay: {
        errors: true,
        warnings: false,
        runtimeErrors: (error) => {
          // 忽略ResizeObserver错误
          if (error?.message?.includes('ResizeObserver loop')) {
            return false;
          }
          return true;
        },
      },
    },
  },
};

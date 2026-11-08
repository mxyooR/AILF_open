// DOM tests use Butterfly doubles and do not draw pixels. Disable jsdom's
// optional native canvas integration, including installs with scripts disabled.
const Module = require('module');
const originalLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === 'canvas') return {};
  return originalLoad.call(this, request, parent, isMain);
};

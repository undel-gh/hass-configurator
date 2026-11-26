/* Ace dynamic modules and workers use the versioned, ingress-relative asset URL. */
(function () {
    'use strict';
    var aceBase = new URL('vendor/ace/', document.currentScript.src).href;
    ['basePath', 'modePath', 'themePath', 'workerPath'].forEach(function (key) {
        ace.config.set(key, aceBase);
    });
})();

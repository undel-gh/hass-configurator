/* First-party Ace policy. The JSON literal is also read by build tooling.
 * #37 phase 1: enforce target worker policy before pruning the archive family.
 * The complete upstream lock remains separate; no retained Ace bytes change.
 */
(function () {
    'use strict';
    var profile = /* HC_WORKER_PROFILE_BEGIN */ {
        "schema": 1,
        "ace_version": "1.45.2",
        "infrastructure": ["worker-base.js"],
        "languages": {
            "ace/mode/css": {"module": "ace/mode/css_worker", "file": "worker-css.js", "class": "Worker"},
            "ace/mode/html": {"module": "ace/mode/html_worker", "file": "worker-html.js", "class": "Worker"},
            "ace/mode/javascript": {"module": "ace/mode/javascript_worker", "file": "worker-javascript.js", "class": "JavaScriptWorker"},
            "ace/mode/json": {"module": "ace/mode/json_worker", "file": "worker-json.js", "class": "JsonWorker"},
            "ace/mode/yaml": {"module": "ace/mode/yaml_worker", "file": "worker-yaml.js", "class": "YamlWorker"}
        },
        "excluded": ["worker-coffee.js", "worker-lua.js", "worker-php.js", "worker-xml.js", "worker-xquery.js"]
    } /* HC_WORKER_PROFILE_END */;
    var aceBase = new URL('vendor/ace/', document.currentScript.src).href;
    ['basePath', 'modePath', 'themePath', 'workerPath'].forEach(function (key) {
        ace.config.set(key, aceBase);
    });

    var byModule = Object.create(null);
    Object.keys(profile.languages).forEach(function (mode) {
        var entry = profile.languages[mode];
        byModule[entry.module] = entry;
    });
    function supportsMode(mode) {
        return Object.prototype.hasOwnProperty.call(profile.languages, mode);
    }
    function checkedWorker(module, classname, workerUrl, imports) {
        var entry = byModule[module];
        if (!entry || (classname !== undefined && classname !== entry.class) || imports) {
            throw new Error('Unsupported Ace worker: ' + module);
        }
        var expected = new URL(entry.file, aceBase).href;
        var resolved = new URL(workerUrl || ace.config.moduleUrl(module, 'worker'), aceBase).href;
        if (resolved !== expected) {
            throw new Error('Unexpected Ace worker URL: ' + module);
        }
        return expected;
    }

    // Ace invokes this hook after setting the actual loaded mode, and when
    // useWorker changes. Preserve the user's preference across mode changes.
    // Unknown and mixed modes are denied by default; HTML's own worker stays.
    var sessionProto = ace.require('ace/edit_session').EditSession.prototype;
    var startWorker = sessionProto.$startWorker;
    sessionProto.$startWorker = function () {
        if (!this.$mode || !supportsMode(this.$mode.$id)) {
            this.$stopWorker();
            this.clearAnnotations();
            return;
        }
        return startWorker.apply(this, arguments);
    };

    // Also constrain the actual client creation path before native Worker or
    // blob creation. Protect against an unexpected module/URL in a retained
    // mode. This is a product policy, not a sandbox for arbitrary page JS.
    var clients = ace.require('ace/worker/worker_client');
    var workerProto = clients.WorkerClient.prototype;
    var createFromConfig = workerProto.$createWorkerFromOldConfig;
    workerProto.$createWorkerFromOldConfig = function (namespaces, module, classname, workerUrl, imports) {
        var url = checkedWorker(module, classname, workerUrl, imports);
        return createFromConfig.call(this, namespaces, module, classname, url);
    };

    // UIWorkerClient uses config.loadModule(["worker", ...]) instead of
    // native Worker. Deny unknown worker modules in that path as well.
    var loadModule = ace.config.loadModule;
    ace.config.loadModule = function (name, callback) {
        if (Array.isArray(name) && name[0] === 'worker') {
            checkedWorker(name[1]);
        }
        return loadModule.apply(this, arguments);
    };

    window.hcAceSupportsWorker = supportsMode;
})();

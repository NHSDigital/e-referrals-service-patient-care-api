"use strict";

const express = require("express");
const app = express();
const log = require("loglevel");
const uuid = require('uuid');



function setup(options) {
    options = options || {};
    app.locals.app_name = options.APP_NAME || 'e-referrals-service-patient-care-api';
    app.locals.version_info = JSON.parse(options.VERSION_INFO || '{}');
    log.setLevel(options.LOG_LEVEL || "info");


    log.info(JSON.stringify({
        timestamp: Date.now(),
        level: "info",
        app: app.locals.app_name,
        msg: "setup",
        version:  app.locals.version_info
    }));
}

function start(options) {
    options = options || {};
    let server = app.listen(options.PORT || 9000, () => {
        log.info(JSON.stringify({
            timestamp: Date.now(),
            level: "info",
            app: app.locals.app_name,
            msg: "startup",
            server_port: server.address().port,
            version:  app.locals.version_info
        }))
    });
    return server;
}

function before_request(req, res, next) {
    res.locals.started_at = Date.now();
    res.locals.correlation_id = (
        req.header('X-Correlation-ID')
        || req.header('Correlation-ID')
        || req.header('CorrelationID')
        || uuid.v4()
    );
    next();
}

const _health_endpoints = ["/_ping", "/health"];

function after_request(req, res, next) {
    if (_health_endpoints.includes(req.path) && !('log' in Object.assign({}, req.query))) {
        // don't log ping / health by default
        return next();
    }
    let finished_at = Date.now();
    let log_entry = {
        timestamp: finished_at,
        level: "info",
        app: app.locals.app_name,
        msg: "request",
        correlation_id: res.locals.correlation_id,
        started: res.locals.started_at,
        finished: finished_at,
        duration: finished_at - res.locals.started_at,
        req: {
            url: req.url,
            method: req.method,
            query: req.query,
            path: req.path,
        },
        res: {
            status: res.statusCode,
            message: res.message
        },
        version: app.locals.version_info
    };

    if (log.getLevel()<2) {
        // debug
        log_entry.req.headers = req.rawHeaders;
        log_entry.res.headers = res.rawHeaders;
    }
    log.info(JSON.stringify(log_entry));

    next();

}

function on_error(err, req, res, next) {
    let log_err = err;
    if (log_err instanceof Error) {
        log_err = {
            name: err.name,
            message: err.message,
            stack: err.stack
        }
    }
    let finished_at = Date.now();
    log.error(JSON.stringify({
        timestamp: finished_at,
        level: "error",
        app: app.locals.app_name,
        msg: "error",
        correlation_id: res.locals.correlation_id,
        started: res.locals.started_at,
        finished: finished_at,
        duration: finished_at - res.locals.started_at,
        err: log_err,
        version:  app.locals.version_info
    }));
    if (res.headersSent) {
        next();
        return;
    }
    res.status(500);
    res.json({error: "something went wrong" });
    next();
}

const handlers = require("./handlers");
app.use(before_request);
app.get("/_ping", handlers.status);
app.get("/_status", handlers.status);
app.get("/health", handlers.status);
app.all("/hello", handlers.hello);
app.use(on_error)
app.use(after_request);

module.exports = {start: start, setup: setup};

"use strict";

const app = require("./app");

app.setup(process.env);

const server = app.start(process.env);


const signals = {
    'SIGHUP': 1,
    'SIGINT': 2,
    'SIGTERM': 15
};

const shutdown = (signal, value) => {
    console.log("shutdown!");
    server.close(() => {
        console.log(`server stopped by ${signal} with value ${value}`);
        process.exit(128 + value);
    });
};

Object.keys(signals).forEach((signal) => {
    process.on(signal, () => {
        console.log(`process received a ${signal} signal`);
        shutdown(signal, signals[signal]);
    });
});


module.exports = {server: server};

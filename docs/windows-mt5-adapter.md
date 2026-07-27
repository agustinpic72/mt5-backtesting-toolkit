# Windows MT5 adapter boundary

`LocalMt5Adapter` is an interface boundary, not an operational MetaTrader launcher.

Version 0.1.0 can:

- require an explicit local-execution opt-in;
- require a Windows platform boundary;
- resolve a terminal executable and tester configuration inside a configured workspace;
- reject missing or invalid files;
- construct a list of process arguments without shell concatenation.

It deliberately cannot:

- launch MetaTrader;
- discover installations, accounts, servers, brokers, or strategies;
- read or inject credentials;
- supply an Expert Advisor, preset, terminal, or market data;
- bypass platform/provider license obligations.

Applications that extend this boundary should keep subprocess invocation out of the shell, enforce a
deadline, check the return code, redact output, isolate generated files, and add explicit cancellation
and cleanup tests. Such an executor must remain opt-in and must never run in this project's CI.

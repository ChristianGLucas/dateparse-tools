"""Shared test helper: a fake AxiomContext."""


class FakeContext:
    """Minimal AxiomContext stand-in, mirroring the real AxiomLogger protocol
    (msg positional, attributes as keywords) so a node that logs with the
    wrong shape fails here instead of at runtime on an error path.
    """

    class _Logger:
        def __init__(self):
            self.records = []

        def debug(self, msg, **attrs): self.records.append(("debug", msg, attrs))
        def info(self, msg, **attrs): self.records.append(("info", msg, attrs))
        def warn(self, msg, **attrs): self.records.append(("warn", msg, attrs))
        def error(self, msg, **attrs): self.records.append(("error", msg, attrs))

    class _Secrets:
        def get(self, name):
            return ("", False)

    def __init__(self):
        self.log = self._Logger()
        self.secrets = self._Secrets()
        self.execution_id = "test-execution-id"
        self.flow_id = "test-flow-id"
        self.tenant_id = "test-tenant-id"

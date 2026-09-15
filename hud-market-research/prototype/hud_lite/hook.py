"""The hook — auto-instrumentation with no code changes.

This is the "cheap on the stack" part. It mirrors the three decisions Hud describes:

  1. Application code only. Frames from site-packages / stdlib are skipped before any work
     is done, because most frames in a real process are library frames and keeping them is
     what makes naive instrumentation expensive.
  2. Durations are incrementally sampled. Early calls are timed, hot calls are timed rarely.
     Cost per call converges toward the cost of one dict lookup and one increment.
  3. Exceptions are NEVER sampled. The product promise is forensics at the moment of failure,
     and a sampled exception is the one crash the agent needed and did not get.

CPython's sys.setprofile is used here because it is stdlib and makes the mechanism legible.
A production sensor would use a lower-overhead path (import-time rewriting, or eBPF — which
is exactly what Hud's "Runtime Internals" job posting points at).
"""

import contextlib
import os
import sys
import threading
import time

from . import store as _store

_state = threading.local()


def _should_time(calls):
    """Incremental sampling: measure a decreasing fraction as call volume grows."""
    if calls < 20:
        return True
    if calls < 200:
        return calls % 10 == 0
    if calls < 2000:
        return calls % 100 == 0
    return calls % 1000 == 0


class Sensor:
    # The sensor must never observe itself. A sensor that instruments its own call path
    # measures its own overhead, recurses into its own store, and drowns the call graph the
    # agent has to read. Every real agent excludes its own package for the same reason it
    # excludes site-packages.
    _SELF_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, app_root, store=None):
        self.app_root = os.path.abspath(app_root)
        self.store = store or _store.RuntimeStore()
        self._installed = False
        # Whether a file belongs to the application never changes, so decide once per file
        # and cache it. On a hot path this turns the filter into a single dict lookup, which
        # is most of the difference between 1-2% overhead and 20%.
        self._files = {}

    # -- filtering -----------------------------------------------------------------

    def _resolve(self, filename):
        """Return (owned, path_relative_to_app_root) for a source file, memoized.

        Paths are reported relative to the application root, never absolute. The consumer of
        this data is an agent that has to open the file in a repo checkout, and an absolute
        path from a production container is meaningless there -- besides leaking the host
        layout into a pull request."""
        cached = self._files.get(filename)
        if cached is not None:
            return cached
        result = (False, None)
        if filename and filename[0] != "<" \
                and "site-packages" not in filename and "dist-packages" not in filename:
            path = os.path.abspath(filename)
            if not path.startswith(self._SELF_DIR) and path.startswith(self.app_root):
                result = (True, os.path.relpath(path, self.app_root))
        self._files[filename] = result
        return result

    def _owns(self, filename):
        return self._resolve(filename)[0]

    @staticmethod
    def _key(code):
        return "%s:%s" % (os.path.basename(code.co_filename), code.co_name)

    # -- the profile callback ------------------------------------------------------

    def _profile(self, frame, event, arg):
        if event != "call" and event != "return":
            return
        code = frame.f_code
        owned, relpath = self._resolve(code.co_filename)
        if not owned:
            return

        stack = getattr(_state, "stack", None)
        if stack is None:
            stack = _state.stack = []

        key = self._key(code)

        if event == "call":
            self.store.record_call(key, relpath, code.co_firstlineno)
            if stack:
                self.store.record_edge(stack[-1][0], key)
            calls = self.store.functions[key]["calls"]
            stack.append((key, time.perf_counter_ns() if _should_time(calls) else None))
        else:
            if not stack:
                return
            popped_key, started = stack.pop()
            if started is not None and popped_key == key:
                self.store.record_duration(key, time.perf_counter_ns() - started)

    # -- lifecycle -----------------------------------------------------------------

    def install(self):
        if self._installed:
            return self
        threading.setprofile(self._profile)
        sys.setprofile(self._profile)
        self._installed = True
        return self

    def uninstall(self):
        sys.setprofile(None)
        threading.setprofile(None)
        self._installed = False
        return self

    # -- exception forensics -------------------------------------------------------

    def capture(self, exc):
        """Record full forensics for one exception. Called at whatever boundary already
        catches errors — a web framework's error handler, a worker's try/except, an
        excepthook. This is what the agent reads later."""
        frames = []
        tb = exc.__traceback__
        while tb is not None:
            f = tb.tb_frame
            owned, relpath = self._resolve(f.f_code.co_filename)
            if owned:
                frames.append({
                    "function": self._key(f.f_code),
                    "file": relpath,
                    "line": tb.tb_lineno,
                    "source": _source_line(f.f_code.co_filename, tb.tb_lineno),
                    # The locals are the single most valuable thing here: they are what a
                    # stack trace alone can never give an agent, and the reason "reproduce
                    # it locally" is not a substitute for a production sensor.
                    "locals": {
                        name: _store.redact(name, value)
                        for name, value in list(f.f_locals.items())[:20]
                    },
                })
            tb = tb.tb_next
        return self.store.record_exception(type(exc).__name__, str(exc), frames)

    @contextlib.contextmanager
    def watching(self):
        """Capture-and-reraise, so instrumenting a call site never changes its behavior."""
        try:
            yield
        except Exception as exc:
            self.capture(exc)
            raise


def _source_line(path, lineno):
    try:
        with open(path) as fh:
            for i, line in enumerate(fh, 1):
                if i == lineno:
                    return line.strip()
    except OSError:
        pass
    return None

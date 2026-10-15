# SPDX-License-Identifier: GPL-2.0-or-later
"""Request lifetime management with injected Qt manager and timer scheduler."""


class ApiTransport:
    def __init__(self, manager, schedule_once):
        self.manager = manager
        self.schedule_once = schedule_once
        self.search_replies = {}
        self.route_reply = None

    def start_search(self, request, request_id, finished, timed_out):
        reply = self.manager.get(request)
        self.search_replies[reply] = request_id
        reply.finished.connect(lambda: finished(reply))
        self.schedule_once(7000, lambda: timed_out(reply))
        return reply

    def start_route(self, request, finished, timed_out=None):
        reply = self.manager.get(request)
        self.route_reply = reply
        reply.finished.connect(lambda: finished(reply))
        if timed_out is not None:
            def expire():
                if self.route_reply is reply:
                    self.cancel_route()
                    timed_out()
            self.schedule_once(30000, expire)
        return reply

    def cancel_route(self):
        reply = self.route_reply
        if reply is None:
            return
        # Clear ownership before abort can cause a synchronous finished callback.
        self.route_reply = None
        self._cancel(reply)

    @staticmethod
    def _cancel(reply):
        try:
            reply.finished.disconnect()
        except (RuntimeError, TypeError):
            pass
        reply.abort()
        reply.deleteLater()

    def close(self):
        self.cancel_route()
        pending = list(self.search_replies)
        self.search_replies.clear()
        for reply in pending:
            self._cancel(reply)

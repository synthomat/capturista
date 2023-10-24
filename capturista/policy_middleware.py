import datetime


class PolicyDecision:
    def __init__(self, result: bool, reason: str = "no reason"):
        self.result = result
        self.reason = reason

    def __repr__(self):
        return f"TimePolicy: {self.result} ({self.reason})"


class TimePolicy:
    def __init__(self, time_range=None):
        self.range = dict(
            start=datetime.datetime.strptime(time_range[0], "%H:%M").time(),
            end=datetime.datetime.strptime(time_range[1], "%H:%M").time()
        )

    def __call__(self):
        now = datetime.datetime.now()
        now_hrs = datetime.time(now.hour, now.minute, 0)

        decision = self.range["start"] < now_hrs < self.range["end"]

        pd = PolicyDecision(decision)

        if not decision:
            pd.reason = "Did not match time"

        return pd


class IPAddressPolicy:
    def __init__(self):
        pass


class PolicyMiddleware:
    def __init__(self, policies):
        self.policies = policies


class AccessMiddleware:
    def __init__(self, app, address_getter=lambda h: False):
        self.app = app
        self.address_getter = address_getter

    def __call__(self, environ, start_response):
        remote_addr = environ.get("REMOTE_ADDR")
        if not self.address_getter(remote_addr):
            return self.app(environ, start_response)

        res = Response(u'Authorization failed', mimetype='text/plain', status=401)
        return res(environ, start_response)

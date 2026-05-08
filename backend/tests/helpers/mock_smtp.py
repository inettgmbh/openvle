"""Mock for SMTP (smtplib.SMTP_SSL / SMTP)."""


class MockSMTP:
    """Mock for smtplib.SMTP_SSL / SMTP."""

    def __init__(self, *args, **kwargs):
        self.sent_messages = []
        self._sendmail_calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def login(self, *args, **kwargs):
        pass

    def starttls(self, *args, **kwargs):
        pass

    def send_message(self, msg):
        self.sent_messages.append(msg)

    def sendmail(self, from_addr, to_addr, msg):
        self._sendmail_calls.append((from_addr, to_addr, msg))
        return {}  # Empty dict = success

    def quit(self):
        pass

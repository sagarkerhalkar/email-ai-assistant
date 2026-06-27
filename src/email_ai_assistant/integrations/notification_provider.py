import sys


class InAppNotificationProvider:
    def notify(self, alert):
        if not alert or not alert.get("shouldNotify"):
            return {"delivered": False, "status": "skipped"}

        if sys.stdout:
            print(f"[notification:{alert.get('channel', 'in_app')}] {alert.get('message')}")
        return {
            "delivered": True,
            "status": "mock_delivered",
            "channel": "in_app",
            "message": alert.get("message"),
        }

"""Notifications. Turn channels on/off in config.json -> notify.providers.

  desktop   Windows pop-up on this PC (free)
  log       appends to orders/notifications.log (free)
  ntfy      push to your phone with the free ntfy app, no account (set env REELFLOW_NTFY_TOPIC to a long random name)
  telegram  message from your own Telegram bot (set REELFLOW_TELEGRAM_TOKEN + REELFLOW_TELEGRAM_CHAT)
  email     via SMTP, e.g. a Gmail app password (set REELFLOW_SMTP_USER + REELFLOW_SMTP_PASSWORD)

Messages to you carry only the order id and style - never the customer's email or video.
"""
import os, smtplib, subprocess, time, urllib.parse, urllib.request
from email.message import EmailMessage
from . import config


def _desktop(cfg, title, body):
    esc = lambda s: s.replace("'", "''")
    ps = ("[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;"
          "$x = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
          "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
          "$t = $x.GetElementsByTagName('text'); $t[0].AppendChild($x.CreateTextNode('" + esc(title) + "')) > $null;"
          "$t[1].AppendChild($x.CreateTextNode('" + esc(body) + "')) > $null;"
          "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
          "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe')"
          ".Show([Windows.UI.Notifications.ToastNotification]::new($x))")
    subprocess.Popen(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)


def _log(cfg, title, body):
    with open(os.path.join(config.path(cfg["queue"]["dir"]), "notifications.log"), "a", encoding="utf-8") as f:
        f.write("%s  %s | %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), title, body))


def _ntfy(cfg, title, body):
    topic = cfg["notify"]["ntfy_topic"]
    if topic:
        urllib.request.urlopen(urllib.request.Request("https://ntfy.sh/" + urllib.parse.quote(topic), data=body.encode(),
                                                      headers={"Title": title, "Priority": "high"}), timeout=15)


def _telegram(cfg, title, body):
    n = cfg["notify"]
    if n["telegram_bot_token"] and n["telegram_chat_id"]:
        data = urllib.parse.urlencode({"chat_id": n["telegram_chat_id"], "text": "%s\n%s" % (title, body)}).encode()
        urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % n["telegram_bot_token"], data, timeout=15)


def send_email(cfg, to, subject, body):
    s = cfg["notify"]["smtp"]
    if not (s["user"] and s["password"] and to):
        return False
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = s["from"] or s["user"], to, subject
    m.set_content(body)
    with smtplib.SMTP(s["host"], int(s["port"]), timeout=30) as c:
        c.starttls()
        c.login(s["user"], s["password"])
        c.send_message(m)
    return True


def _email(cfg, title, body):
    send_email(cfg, cfg["notify"]["smtp"]["user"], title, body)


CHANNELS = {"desktop": _desktop, "log": _log, "ntfy": _ntfy, "telegram": _telegram, "email": _email}


def owner(title, body, cfg=None):
    """Notify the business owner on every enabled channel; one failing channel never blocks the others."""
    cfg = cfg or config.load()
    for name in cfg["notify"]["providers"]:
        try:
            CHANNELS[name](cfg, title, body)
        except Exception as e:  # noqa: BLE001
            try:
                _log(cfg, "notify-%s failed" % name, repr(e))
            except OSError:
                pass

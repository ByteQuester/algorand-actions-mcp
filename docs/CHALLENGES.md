# Upgrade and Catchup Challenges (Resolved)

Environment: Debian 11 (bullseye), systemd `algorand.service`, data dir `/var/lib/algorand`.

1) APT upgrade failed (`control.tar.zst`)
- dpkg on bullseye lacks zstd control support.
- Switched to official updater:
  curl -fsSLO https://raw.githubusercontent.com/algorand/go-algorand/rel/stable/cmd/updater/update.sh
  chmod +x update.sh
  sudo /tmp/update.sh -i -c stable -d /var/lib/algorand

2) Updater needed explicit data dir
- Pass: -d /var/lib/algorand

3) systemd still used old /usr/bin/algod
- Added drop-in override to ExecStart=/var/lib/algorand/algod -d /var/lib/algorand and daemon-reload.

4) Stale lock prevented start
- Stop, kill stray algod, rm /var/lib/algorand/algod.lock, start.

5) Fast catchup
- Fetch latest catchpoint and run goal node catchup; status shows progress.

Current: 4.2.1.stable, service active, catchup running to latest catchpoint.

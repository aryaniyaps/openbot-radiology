#!/usr/bin/env bash
# Operator launcher only. All agent behavior is configured in OpenMausBot.
set -euo pipefail
demo_home=/home/kauvery-demo
demo_uid=$(id -u kauvery-demo)
if [[ -z "${DISPLAY:-}" || -z "${XAUTHORITY:-}" ]]; then
  echo 'Launch from the signed-in Linux desktop (DISPLAY and XAUTHORITY required).' >&2
  exit 1
fi
sudo -n install -m 600 -o kauvery-demo -g kauvery-demo \
  "$XAUTHORITY" "$demo_home/.Xauthority"
exec sudo -n -u kauvery-demo env -i \
  HOME="$demo_home" USER=kauvery-demo LOGNAME=kauvery-demo \
  PATH=/opt/kauvery-demo/bin:/usr/local/bin:/usr/bin:/bin \
  CODEX_HOME="$demo_home/.codex" DISPLAY="$DISPLAY" \
  XDG_RUNTIME_DIR="/run/user/$demo_uid" \
  DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$demo_uid/bus" \
  XAUTHORITY="$demo_home/.Xauthority" \
  /bin/sh -c 'cd /home/kauvery-demo && exec "$@"' sh \
  /opt/OpenMausBot/openmausbot --ozone-platform=x11 "$@"

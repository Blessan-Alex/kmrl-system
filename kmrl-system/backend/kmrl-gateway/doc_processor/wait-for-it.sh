#!/bin/sh
set -e
host="$1"; shift
# If next arg is a number, treat it as port; otherwise default to 9000
case "$1" in
  ''|*[!0-9]*) port="9000" ;;
  *) port="$1"; shift ;;
esac
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "$host:$port is unavailable - sleeping"
  sleep 1
done

>&2 echo "$host:$port is up - ready"
if [ -n "$cmd" ]; then
  exec $cmd
fi
exit 0
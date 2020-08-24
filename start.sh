#!/bin/sh

CMD=$1; shift
case "$CMD" in
web)
    exec python -m captain.main "$@"
    ;;
asset)
    exec python -m skyfarer.main "$@"
    ;;
*)
    >&2 echo "Usage: docker ... [web|asset] [args ...]"
    exit 1
esac

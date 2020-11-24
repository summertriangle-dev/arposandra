#!/bin/sh
REF=$(git describe --always)
sed -i'' -E "s|: (.+) # @exp_as_git_rev@|: \"$REF\" # @exp_as_git_rev@|" docker-compose.yml \
    && ( rm -f docker-compose.yml.next || true )

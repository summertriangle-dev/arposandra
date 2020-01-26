#!/bin/sh
REF=$(git describe --always)
sed -i.next -E "s|: (.+) # @exp_as_git_rev@|: $REF # @exp_as_git_rev@|" docker-compose.yml

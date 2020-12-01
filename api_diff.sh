#!/bin/env bash
new_commit=$1
old_commit=$2

function parse_handler() {
  row=$1
  version=$2
  pattern='([+|-])\W+route\.NewRoute\(version, http\.Method(.+), \"\/(.+)\", .+\),'
  if [[ ${row} =~ $pattern ]] ; then
    mode=${BASH_REMATCH[1]}
    path=${BASH_REMATCH[3]}

    if [[ "$mode" = "+" ]]
    then
      mode="added"
    elif [[ "$mode" = "-" ]]
    then
      mode="removed"
    fi

    echo "$version;$mode;/$path;$path.go"
  fi
}

function parse_file() {
  row=$1
  version=$2
  pattern='([A-Z])\W+src/smarpshare/versioningapi/'${version}'/(.+).go'
  if [[ ${row} =~ $pattern ]] ; then
    mode=${BASH_REMATCH[1]}
    path=${BASH_REMATCH[2]}

    if [[ "$mode" = "A" ]]
    then
      mode="added"
    elif [[ "$mode" = "C" ]]
    then
      mode="modified"
    elif [[ "$mode" = "D" ]]
    then
      mode="removed"
    elif [[ "$mode" = "M" ]]
    then
      mode="modified"
    elif [[ "$mode" = "R" ]]
    then
      mode="modified"
    elif [[ "$mode" = "T" ]]
    then
      mode="modified"
    fi

    echo "$version;$mode;/$path;$path.go"
  fi
}

function get_diff() {
  new_commit=$1
  old_commit=$2
  version=$3
  diff=$(git diff --output-indicator-context="=" "${new_commit}" "${old_commit}" -- src/smarpshare/versioningapi/"${version}"/router.go)
#  echo $diff
  IFS=$'\n'
  for item in $diff
  do
    parse_handler "${item}" "${version}"
  done

  diff=$(git diff-tree --no-commit-id --name-status -r "${new_commit}^..${old_commit}" -- src/smarpshare/versioningapi/"${version}"/*.go | grep -v "_test.go" | grep -v "router.go")
#  echo $diff
  for item in $diff
  do
    parse_file "${item}" "${version}"
  done
}

function scan_api() {
  new_commit=$1
  old_commit=$2
  rls=$(ls src/smarpshare/versioningapi | grep -E "v[0-9]+")
  for i in $rls; do get_diff "$new_commit" "$old_commit" "$i" | uniq ; done;
}

cd /home/gollariel/go/src/git.smarpsocial.com/smarp/backend || exit 1
scan_api "$1" "$2"
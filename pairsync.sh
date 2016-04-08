#!/bin/bash

if [[ -z $(git status | grep "On branch feature") ]]; then
	echo "This is not a feature branch!"
	exit 1
fi

git add .
git ci -m "WIP"
git push


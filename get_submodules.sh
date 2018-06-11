#!/bin/bash
# Install ssh-agent if not already installed, it is required by Docker.
# (change apt-get to yum if you use a CentOS-based image)

which ssh-agent || ( apt-get update -y && apt-get install openssh-client -y )

# Run ssh-agent (inside the build environment)
eval $(ssh-agent)

# Add the SSH key stored in SSH_PRIVATE_KEY variable to the agent store
#ssh-add <$(echo "$SSH_PRIVATE_KEY")
echo "$SSH_PRIVATE_KEY" | ssh-add -

# For Docker builds disable host key checking. Be aware that by adding that
# you are suspectible to man-in-the-middle attacks.
# WARNING: Use this only with the Docker executor, if you use it with shell
# you will overwrite your user's SSH config.

mkdir -p ~/.ssh
echo -e "Host *\n\tStrictHostKeyChecking no\n\n" > ~/.ssh/config

git config --global submodule.fetchJobs 10
git submodule update --init
git submodule sync --recursive
git submodule update --init --recursive

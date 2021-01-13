#!/bin/bash
set -e

was_changed () {
   list=$(git diff --name-only --diff-filter=ADMR @~..@ | grep -e "v[0-9]")
   echo $?
}

create_tag () {
    TAG="$(date '+%d-%m-%Y')-$(printf '%x\n' $(date +%s))"
    git config --global user.email $GITLAB_USER_EMAIL
    git config --global user.name $GITLAB_USER_NAME
    git remote set-url origin https://$PUSH_ACCESS_TOKEN_NAME:$PUSH_ACCESS_KEY_TOKEN@git.smarpsocial.com/smarp/common.git
    git tag -a "${TAG}" -m "$(git log -1 --pretty=%s)"
    git push origin --tags
    echo $TAG
}

slack_message() {
  #Send Slack message
  SLACK_MSG="$CI_PROJECT_NAME was deployed. $CI_PROJECT_URL/tags/$1 ($CI_COMMIT_SHORT_SHA) "
  curl https://slack.com/api/chat.postMessage -X POST -d "as_user=false" -d "username=$GITLAB_USER_NAME" -d "channel=$ANNOUNCEMENT_CHANNEL" -d "token=$SLACK_BOT_TOKEN" -d "text=$SLACK_MSG" -d "icon_emoji=$PROJECT_EMOJI"
}

retVal=$(was_changed)
echo "git command retVal : ${retVal}"
if [ $retVal -eq 0 ]; then
  TAG=$(create_tag)
  slack_message "${TAG}"
else
  echo "no match found for the folder/file : $1"
fi
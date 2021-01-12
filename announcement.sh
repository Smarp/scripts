#!/bin/bash
set -e

was_changed () {
   list=$(git diff --name-only --diff-filter=ADMR @~..@ | grep -e "v[0-9]")
   echo $?
}

create_tag () {
    git config --global user.email $GITLAB_USER_EMAIL
    git config --global user.name $GITLAB_USER_NAME
    git remote set-url origin https://$PUSH_ACCESS_TOKEN_NAME:$PUSH_ACCESS_KEY_TOKEN@git.smarpsocial.com/smarp/common.git
    git tag -a "$(date '+%d-%m-%Y')-$(printf '%x\n' $(date +%s))" -m "$(git log -1 --pretty=%s)"
    git push origin --tags
}

slack_message() {
  #Send Slack message
  SLACK_MSG="$CI_PROJECT_NAME *$CI_COMMIT_TAG* was deployed to *$STAGE*. $CI_PROJECT_URL/tags/$CI_COMMIT_TAG ($CI_COMMIT_SHORT_SHA) "
  curl https://slack.com/api/chat.postMessage -X POST -d "as_user=false" -d "username=$GITLAB_USER_NAME" -d "channel=$ANNOUNCEMENT_CHANNEL" -d "token=$SLACK_BOT_TOKEN" -d "text=$SLACK_MSG" -d "icon_emoji=$PROJECT_EMOJI"
}

retVal=$(was_changed)
echo "git command retVal : ${retVal}"
if [ $retVal -eq 0 ]; then
  create_tag
  slack_message
else
  echo "no match found for the folder/file : $1"
  exit $retVal
fi
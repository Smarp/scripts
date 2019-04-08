#! /bin/bash
set -v
set -e
deployedTo=$STAGE;

if [ -n "$DEPLOYMENT_NAME" ]; then
 deployedTo=$DEPLOYMENT_NAME
fi

#Send Slack message
SLACK_MSG="$CI_PROJECT_NAME *$CI_COMMIT_TAG* was deployed to *$deployedTo*. $CI_PROJECT_URL/tags/$CI_COMMIT_TAG ($CI_COMMIT_SHORT_SHA)"
echo $SLACK_MSG
curl https://slack.com/api/chat.postMessage -X POST -d "as_user=false" -d "username=$GITLAB_USER_NAME" -d "channel=$ANNOUNCEMENT_CHANNEL" -d "token=$SLACK_BOT_TOKEN" -d "text=$SLACK_MSG" -d "icon_emoji=$PROJECT_EMOJI"
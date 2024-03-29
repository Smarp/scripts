#! /bin/bash
set -v
set -e
#Send Slack message
SLACK_MSG="$CI_PROJECT_NAME *$CI_COMMIT_TAG* was deployed to *$STAGE*. $CI_PROJECT_URL/-/releases/$CI_COMMIT_TAG ($CI_COMMIT_SHORT_SHA) "
curl https://slack.com/api/chat.postMessage -X POST -d "as_user=false" -d "username=$GITLAB_USER_NAME" -d "channel=$ANNOUNCEMENT_CHANNEL" -d "token=$SLACK_BOT_TOKEN" -d "text=$SLACK_MSG" -d "icon_emoji=$PROJECT_EMOJI"

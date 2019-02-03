#! /bin/bash
set -v
set -e
#Send Slack message
SLACK_MSG=":rocket: $CI_PROJECT_NAME *$CI_COMMIT_REF_NAME* was deployed to *$STAGE*. https://git.smarpsocial.com/smarp/$CI_PROJECT_NAME/tags/$CI_COMMIT_REF_NAME ($CI_COMMIT_SHORT_SHA) "
echo $SLACK_MSG
curl https://slack.com/api/chat.postMessage -X POST -d "as_user=false" -d "username=$GITLAB_USER_NAME" -d "channel=$ANNOUNCEMENT_CHANNEL" -d "token=$SLACK_BOT_TOKEN" -d "text=$SLACK_MSG"

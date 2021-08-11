"""Script parses changelog from git based on 2 latest tags, formates changelog to .md format, creates/updates release on gitlab
"""
import subprocess
import os
import re
import json

def convert_api_diff_changed_to_md (new_commit, old_commit) :
    exists = False
    res = ""
    rls = [f for f in os.listdir('src/smarpshare/versioningapi') if re.match(r'v[0-9]+', f)]
    for version in rls :
        res += build_header_issue("API "+version+" changes")
        diff_api_handlers_cmd = 'git diff '+new_commit+' '+old_commit+' -- src/smarpshare/versioningapi/'+version+'/router.go'
        diff_api_files_cmd = 'git diff-tree --no-commit-id --name-status -r '+new_commit+'^..'+old_commit+' -- src/smarpshare/versioningapi/'+version+'/*.go'

        diff_api_handlers = run_command(diff_api_handlers_cmd)
        result = re.findall(r'([+|-])\W+route\.NewRoute\(version, http\.Method(.+), \"\/(.+)\", .+\),', diff_api_handlers, re.MULTILINE)
        for mt in result :
            if mt[0] == "+":
                mode = "added"
            else:
                mode = "removed"
            path = mt[2]
            txt = 'Endpoint /'+path+' was '+mode
            res += build_issue(txt)
            exists = True

        diff_api_files = run_command(diff_api_files_cmd)
        result = re.findall(r'([A-Z])\W+src/smarpshare/versioningapi/'+version+'/(?!schema/|handler|router|.+_test)(.+)\.go', diff_api_files, re.MULTILINE)
        for mt in result :
            if mt[0] == "A":
                mode = "added"
            elif mt[0] == "C":
                mode = "modified"
            elif mt[0] == "D":
                mode = "removed"
            elif mt[0] == "M":
                mode = "modified"
            elif mt[0] == "R":
                mode = "modified"
            elif mt[0] == "T":
                mode = "modified"
            else:
                mode = "unchanged"
            path = mt[1]
            txt = 'Endpoint /'+path+' was '+mode
            if not txt in res :
                res += build_issue(txt)
                exists = True

    if not exists:
        res = ""

    return res

def get_files_changed(new_commit,old_commit) :
    bash_command = 'git diff --name-only ' + new_commit+ ' ' + old_commit
    return run_command(bash_command)

def get_md_formatted_changelog(new_commit, old_commit) :
    #saving parameters this way to make sure that they are read properly on bash command
    get_log_format = '%x1f'.join(['%b', '%h']) + '%x1e'
    bash_command = 'git --no-pager --git-dir=.git log --merges --format="%s"' % get_log_format   + " "+ new_commit+"..." + old_commit
    #getting raw changelog from git

    raw_changelog = run_command(bash_command).replace("\"", "").replace("\'", "")
    md_formatted_changelog =  convert_changelog_text_to_md(raw_changelog, None)

    # finding changed sql files in git
    all_files_changed = get_files_changed(new_commit, old_commit).lower()
    sql_files_changed = re.compile("sql\/diff.*.sql").findall(all_files_changed)
    sql_diff_changed_md = convert_sql_diff_changed_to_md(sql_files_changed)
    api_diff_changed_md = convert_api_diff_changed_to_md(new_commit, old_commit)
    return md_formatted_changelog + sql_diff_changed_md + api_diff_changed_md

def build_command_for_delete_release(tag) :
    formatted_project_path = os.environ['CI_PROJECT_PATH'].replace("/","%2F")
    return 'curl --request DELETE --header "PRIVATE-TOKEN: $GITLAB_API_PRIVATE_TOKEN" "https://git.smarpsocial.com/api/v4/projects/'+formatted_project_path+'/releases/' + tag +'"'

def build_command_for_create_release(clean_changelog,tag) :
    formatted_project_path = os.environ['CI_PROJECT_PATH'].replace("/","%2F")
    data = {"name": tag,"tag_name": tag,"description": clean_changelog}
    encodedData =  json.dumps(data)
    return 'curl --header "Content-Type: application/json" --header "PRIVATE-TOKEN: $GITLAB_API_PRIVATE_TOKEN"  --data \''+encodedData+'\'   --request POST "https://git.smarpsocial.com/api/v4/projects/'+formatted_project_path+'/releases/"'

def put_tag_notes_on_gitlab( clean_changelog  , tag):
    print("removing existing release: "+ tag)
    k = os.system(build_command_for_delete_release(tag))
    print("creating new release: "+ tag)
    k = os.system(build_command_for_create_release(clean_changelog, tag))
    print("\n")

def run_command( bash_command ):
    """Sends command to system.
    """
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error is not None :
        print(error)
        print("Terminating...")
        quit()
    return output.strip('\n')

def get_commit_by_tag( tag ):
    return  run_command("git rev-list -n 1 " +  tag)

def parse_raw_changelog(non_formatted_text ) :
    """Parses raw changelog extracted from git.
     Returns map {'issue_type': ['issues_array']}
    """
    mapped_issues = {}
    for line in non_formatted_text.splitlines() :
        #skipping empty lines, non related to issues description lines, etc...
        if line == "" :
            continue
        if line.startswith("See merge request") or line.startswith("This reverts commit"):
            continue
        if len(line)<=11 and not " " in line:
            continue
        categorized_issue = False
        for issue_type in issue_types:
            issue_prefix = issue_type + ": "
            #checking lower cased strings to prevent skipping misnamed issues
            if line.strip(" ").lower().startswith(issue_prefix.lower()) :
                categorized_issue = True
                line = line.replace(issue_prefix, "")
                if issue_type not in mapped_issues :
                    mapped_issues.update({issue_type : [line]})
                else:
                    mapped_issues[issue_type].append(line)
                break
        if categorized_issue :
            continue
        #if code reach that line - means issue type is not in issue_types -> typo or uncategorized issuetype
        if uncategorized_issueType not in mapped_issues :
            mapped_issues.update({uncategorized_issueType : [line]})
        else:
            mapped_issues[uncategorized_issueType].append(line)
        continue
    return mapped_issues

line_breaker = "\n"
issue_types = {"Enhancement","Fix", "Feature", "Ongoing", "Checkmark",
               "Related", "Lab", "Live", "Refactor", "Nochangelog", "Technical"}

uncategorized_issueType = "Uncategorized"

def convert_sql_diff_changed_to_md(files) :
    if len(files) == 0 :
        return ""
    res = build_header_issue("Database changes")
    for file in files :
        res += build_issue(file)
    return res

def convert_changelog_text_to_md(non_formatted_text , header ) :
    """Returns .MD formatted changelog based on raw formatted text.
     Header - 'title' for set of issues in that changelog
    """
    mapped_issues = parse_raw_changelog(non_formatted_text)
    if len(mapped_issues) == 0 :
        return ""
    res = ""
    if not (not header or header == ""):
        res += build_header_project(header) + line_breaker
    res += build_changelog_body(mapped_issues)
    return res

def build_header_project(header )  :
    return "## " + header + line_breaker

def build_header_issue(header )  :
    return "### " + header + ":" + line_breaker

def build_issue(issue ) :
    return " - " + issue + line_breaker

def build_changelog_body(mapped_issues)  :
    res = ""
    for issue_type  in  mapped_issues :
        res += build_header_issue(issue_type)
        for issue in mapped_issues[issue_type] :
            res += build_issue(issue)
        res += line_breaker
    return res

def main():
    new_commit = os.environ['CI_COMMIT_SHA']
    old_commit = ""

    there_is_a_tag = "CI_BUILD_TAG" in os.environ
    there_is_a_release_tag = there_is_a_tag and os.environ["CI_BUILD_TAG"].endswith("-rc")
    there_is_a_sos_tag = there_is_a_tag and os.environ["CI_BUILD_TAG"].endswith("-sos")

    # development branch
    if not there_is_a_tag:
        print "development case"
        old_tag = run_command("git describe --abbrev=0 --tags --match v*-rc ")

    # release case
    if there_is_a_release_tag:
        print "release case"
        new_tag = os.environ["CI_BUILD_TAG"]
        old_tag = run_command("git describe --abbrev=0 --tags "+ new_tag +"^ --match v*[0-9]-rc")

    # sos case
    if there_is_a_sos_tag:
        print "sos case"
        new_tag = os.environ["CI_BUILD_TAG"]
        old_tag = run_command("git describe --abbrev=0 --tags "+ new_tag +"^ --match v*[0-9]")

    # master case
    if there_is_a_tag and not there_is_a_release_tag and not there_is_a_sos_tag:
        print "master case"
        new_tag = os.environ["CI_BUILD_TAG"]
        old_tag = run_command("git describe --abbrev=0 --tags "+ new_tag +"^ --match v*[0-9]")

    old_commit = get_commit_by_tag(old_tag)
    print "comparing commits: " + new_commit + "..." + old_commit
    md_formatted_changelog = get_md_formatted_changelog(new_commit, old_commit)

    print( md_formatted_changelog)
    if there_is_a_tag:
        put_tag_notes_on_gitlab(md_formatted_changelog, new_tag)

if __name__ == "__main__":
    main()

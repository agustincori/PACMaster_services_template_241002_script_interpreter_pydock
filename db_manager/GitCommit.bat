@echo off

REM Your GitHub username
set GITHUB_USERNAME=agustincori

REM Your repository name
set REPO_NAME=PACMasterDB

REM Initializing Git repository...
git init

REM Adding all files to the staging area...
git add .

REM Request input for the commit message
set /p COMMIT_MESSAGE="Enter the initial commit message: "

REM Committing changes with the message "%COMMIT_MESSAGE%"...
git commit -m "%COMMIT_MESSAGE%"

pause > nul

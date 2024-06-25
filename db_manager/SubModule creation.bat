@echo off
REM Change directory up one level to ensure we're in the correct parent repository root
cd..

REM Remove the existing directory from Git's tracking, without deleting the files themselves
git rm --cached PACMasterDB -r

REM Commit the removal to the repository, making the state without the submodule official
git commit -m "Remove PACMasterDB to add as submodule"

REM Add the submodule to the repository at the specified path, setting up tracking
git submodule add ./PACMasterDB PACMasterDB

REM Initialize the submodule configuration, preparing Git to track the submodule
git submodule init

REM Update the submodule, actually fetching and checking out the content at the commit specified by the parent repo
git submodule update
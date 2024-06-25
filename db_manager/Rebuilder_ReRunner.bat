@echo off
REM Stop and remove the Docker container
docker stop 240214_PACMasterDB_pydock
docker rm -f 240214_PACMasterDB_pydock

REM Call the builder and runner batch files
call 240214_pacmasterdb_pydock_builder.bat
call 240214_pacmasterdb_pydock_runner.bat

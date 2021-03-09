@echo off
if not DEFINED IS_MINIMIZED set IS_MINIMIZED=1 && start "" /min "%~dpnx0" %* && exit
set root=C:\Anaconda3
set file_path=%~dp0main.py
call %root%\Scripts\activate.bat %root%
call conda activate tf22-py37
call python %file_path%
exit
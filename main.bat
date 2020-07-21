@echo off
set root=C:\Anaconda3
set file_path=%~dp0main.py
call %root%\Scripts\activate.bat %root%
call conda activate tf22-py37
call python %file_path%
exit
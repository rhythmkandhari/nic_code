@echo off
rem Starts GovINTEL.AI with the project's venv, whatever environment the terminal has active
rem (conda's label-studio env lacks the CUDA libraries, so the model would run slowly there).
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" -m streamlit run final.py %*

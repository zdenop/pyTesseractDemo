@ECHO OFF

:Loop
IF "%1"=="clean" GOTO clean
IF "%1"=="build" GOTO build

:clean
  rm -f  lib/*.pyc ui/*.pyc ui/ui_*.py resources*.py *.pyc

:build
(
  echo Building...
  CALL pyuic4 ui/MainWindow.ui > ui/ui_mainwindow.py
  CALL pyrcc4 resources.qrc -o resources_rc.py
  GOTO end
  REM EXIT /B 0
)

:end
 echo Done!

@ECHO OFF

:Loop
IF "%1"=="clean" GOTO clean
IF "%1"=="build" GOTO build

:clean
  rm -f  ui/ui_*.py resources*.py

:build
(
  echo Building...
  CALL pyuic5 ui/MainWindow.ui > ui/ui_mainwindow.py
  CALL pyrcc5 resources.qrc -o resources_rc.py
  GOTO end
  REM EXIT /B 0
)

:end
 echo Done!

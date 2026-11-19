@echo off
REM 一键编译并运行（需要 JDK 17+）
setlocal
if not exist build mkdir build
javac -encoding UTF-8 -d build src\*.java
if errorlevel 1 (
    echo compile failed
    exit /b 1
)
echo compiled, starting LoginGUI ...
java -cp build LoginGUI
endlocal

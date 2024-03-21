docker build -t hammerpy .

unameOut="$(uname -s)"
if [ "$unameOut" = "Darwin" ]
then
    echo "macOS detected. XQuartz install will be checked so HammerPy can emulate the X window system."
    brew install --cask xquartz
    defaults write org.xquartz.X11.plist nolisten_tcp -bool false
fi
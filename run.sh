docker build -t hammerpy .

unameOut="$(uname -s)"
ip=""
if [ "$unameOut" = "Darwin" ]
then
    echo "macOS detected. XQuartz will be installed so HammerPy can emulate the X window system."
    brew install --cask xquartz
    defaults write org.xquartz.X11.plist nolisten_tcp -bool false
    ip="$(ipconfig getifaddr en0)"
    open -a XQuartz
    xhost +
else
    ip="$(hostname -i)"
fi

docker run -it -u=$(id -u $USER):$(id -g $USER) \
           -e DISPLAY=host.docker.internal:0 \
           -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
           -v $(pwd) \
           hammerpy
unameOut="$(uname -s)"
if [ "$unameOut" = "Darwin" ]
then
    open -a XQuartz
    xhost +
    docker run -it -u=$(id -u $USER):$(id -g $USER) \
           -e DISPLAY=host.docker.internal:0 \
           -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
           -v $(pwd) \
           hammerpy
else
    docker run -it -u=$(id -u $USER):$(id -g $USER) -P \
           -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
           -v $(pwd) \
           hammerpy
fi
FROM nodejs as builder
# build label studio frontend here

FROM heartexlabs/label-studio:latest
# copy labelstudio frontend directory here
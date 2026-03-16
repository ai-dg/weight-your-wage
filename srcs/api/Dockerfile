# TODO: remplacer par l'image et la config réelles
FROM debian:latest

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y curl && curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH=$PATH:/root/.local/bin 


CMD ["sleep", "infinity"]

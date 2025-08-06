

FROM python:3.10-slim

WORKDIR /build
COPY . .

RUN pip install pyinstaller && \
    pyinstaller --onefile \
      --name scaleforge \
      --add-data "src/scaleforge/models/model_registry.json:scaleforge/models" \
      src/scaleforge/cli/main.py

ENTRYPOINT ["/build/dist/scaleforge"]


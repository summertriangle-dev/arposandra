# 1. css/js needs to be built with Webpack
FROM node:12-alpine AS js-builder

WORKDIR /usr/kars-fe-build
COPY ./frontend/package.json ./frontend/yarn.lock /usr/kars-fe-build/
RUN yarn

COPY ./frontend /usr/kars-fe-build
RUN mkdir -p static/css static/js
RUN yarn run node-sass css/theme-dark.scss static/css/theme-dark.css \
    && yarn run node-sass css/theme-light.scss static/css/theme-light.css
RUN yarn run webpack --display-modules --output-path static/js

# 2. Build wheels
FROM python:3.9 as extension-builder

RUN mkdir /install
WORKDIR /build

COPY ./requirements.txt /build/requirements.txt
RUN pip --no-cache-dir install --prefix=/install -r /build/requirements.txt
COPY ./skyfarer/hwdecrypt_src /build/hwdecrypt_src
RUN pip --no-cache-dir install --prefix=/install ./hwdecrypt_src
COPY ./maintenance/lib /build/lib
# astool is an optional dependency... or so we say.
RUN (test -f /build/lib/setup.py && pip --no-cache-dir install --prefix=/install "./lib[async_pkg]")

# 3. Copy all in
FROM python:3.9-slim

WORKDIR /usr/kars

COPY . /usr/kars
COPY --from=extension-builder /install /usr/local
COPY --from=js-builder /usr/kars-fe-build/static/js ./captain/static/js
COPY --from=js-builder /usr/kars-fe-build/static/css/* ./captain/static/css/

RUN mkdir -p /external/astool_storage
RUN chmod 777 /external/astool_storage

USER 501:501

ARG AS_GIT_REVISION
ENV AS_GIT_REVISION ${AS_GIT_REVISION}

ENV ASTOOL_STORAGE /external/astool_storage
ENV AS_ASSET_ADDR 0.0.0.0
ENV AS_ASSET_PORT 30001
ENV AS_DATA_ROOT /external/astool_storage
ENV AS_WEB_ADDR 0.0.0.0
ENV AS_WEB_PORT 30001
ENV LIVE_MASTER_CHECK_ALLOWED 1

ENTRYPOINT ["./start.sh"]

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
FROM python:3.7 as extension-builder

WORKDIR /build
COPY ./skyfarer/hwdecrypt_src /build/hwdecrypt_src
RUN (cd hwdecrypt_src && python setup.py clean bdist_wheel)

# 3. Copy all in
FROM python:3.7-slim

WORKDIR /usr/kars
COPY ./requirements.txt /usr/kars/requirements.txt
COPY --from=extension-builder /build/hwdecrypt_src/dist/hwdecrypt*.whl /tmp/wheels/
RUN pip3 --no-cache-dir install /tmp/wheels/*.whl -r requirements.txt && rm -rf /tmp/wheels

COPY . /usr/kars
RUN ( cd maintenance/lib && python -m pip --no-cache-dir install '.[async_pkg]' )

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

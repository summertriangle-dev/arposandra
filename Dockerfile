# 1. css/js needs to be built with Webpack
FROM node:12-alpine AS js-builder
RUN apk add make

COPY ./frontend/package.json ./frontend/yarn.lock /usr/kars-fe-build/
WORKDIR /usr/kars-fe-build
RUN yarn

COPY ./frontend /usr/kars-fe-build
RUN mkdir static
RUN CSS_TARGET_DIR=./static/css JS_TARGET_DIR=./static/js make all

# 3. Copy all in
FROM python:3.7-slim

WORKDIR /usr/kars
COPY ./requirements.txt /usr/kars/requirements.txt
RUN pip3 --no-cache-dir install -r requirements.txt

COPY . /usr/kars
COPY --from=js-builder /usr/kars-fe-build/static/js ./captain/static/js
COPY --from=js-builder /usr/kars-fe-build/static/css/* ./captain/static/css/

RUN mkdir -p /external/assets
RUN chmod 777 /external/assets

USER 501:501
ARG AS_GIT_REVISION
ENV AS_GIT_REVISION ${AS_GIT_REVISION}
CMD ["python", "./start_web.py"]

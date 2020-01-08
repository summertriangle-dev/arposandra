CSS_TARGET_DIR ?= ../captain/static/css
JS_TARGET_DIR ?= ../captain/static/js

.phony: sass-watch js-watch webpack-release
all: $(CSS_TARGET_DIR)/theme-dark.css $(CSS_TARGET_DIR)/theme-light.css webpack-release

$(CSS_TARGET_DIR)/theme-light.css: css/theme-light.scss
	mkdir -p $(CSS_TARGET_DIR)
	yarn run   node-sass --omit-source-map-url $< $@

$(CSS_TARGET_DIR)/theme-dark.css: css/theme-dark.scss
	mkdir -p $(CSS_TARGET_DIR)
	yarn run   node-sass --omit-source-map-url $< $@

webpack-release:
	yarn run   webpack --config webpack.config.js --mode=production --display-modules --output-path $(JS_TARGET_DIR) --output-public-path /static/js/

sass-watch:
	yarn run   node-sass --watch  --output $(CSS_TARGET_DIR) css

js-watch:
	yarn run   webpack-dev-server --config webpack.config.js --output-path $(JS_TARGET_DIR)
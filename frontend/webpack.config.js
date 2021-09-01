const webpack = require("webpack")
const process = require("process")

const resolve = () => {
    if (process.env.NODE_ENV === "development") {
        return {}
    }

    return {alias: {
        "react": "preact/compat",
        "react-dom/test-utils": "preact/test-utils",
        "react-dom": "preact/compat",
    }}
}

module.exports = {
    mode: "production",
    entry: {
        "early": "./js/entry.js",
        "main": "./js/late_entry.js",
    },
    output: {
        filename: "[name].bundle.js",
        chunkFilename: "[name].bundle.js?v=[chunkhash:8]",
        sourceMapFilename: "[name].bundle.js.map",
        publicPath: process.env["WDS_PUBLIC_PATH"] || "/static/js/",
    },
    module: {
        rules: [{
            test: /\.js$/,
            exclude: [/node_modules/],
            use: {
                loader: "babel-loader",
                options: {
                    presets: ["@babel/react"],
                    plugins: ["@babel/plugin-syntax-dynamic-import"]
                }
            }
        }, ]
    },
    devtool: "source-map",
    devServer: {
        compress: true,
        host: "0.0.0.0",
        port: 5002,
        headers: {
            "Access-Control-Allow-Origin": "*"
        },
        allowedHosts: "all",
    },
    optimization: {
        splitChunks: {
            chunks: "all",
            // restore webpack 4 vendor chunk names
            // https://stackoverflow.com/questions/66986664/webpack-5-vendors-chunks-naming
            name: (module, chunks, cacheGroupKey) => {
                const allChunksNames = chunks.map((chunk) => chunk.name).join('~');
                const prefix = cacheGroupKey === 'defaultVendors' ? 'vendors' : cacheGroupKey;
                return `${prefix}~${allChunksNames}`;
            },
        },
        runtimeChunk: "single",
    },
    plugins: [
        new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, /en|ja/)
    ],
    resolve: resolve()
}

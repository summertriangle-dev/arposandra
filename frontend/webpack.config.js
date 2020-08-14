const webpack = require("webpack")
const process = require("process")

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
        rules: [
            {
                test: /\.js$/,
                exclude: [/node_modules/],
                use: {
                    loader: "babel-loader",
                    options: {
                        presets: ["@babel/react"],
                        plugins: ["@babel/plugin-syntax-dynamic-import"]
                    }
                }
            },
        ]
    },
    devtool: "source-map",
    devServer: {
        compress: true,
        host: "0.0.0.0",
        port: 5002,
        headers: {"Access-Control-Allow-Origin": "*"},
        disableHostCheck: true,
    },
    optimization: {
        splitChunks: { chunks: "all" }
    },
    plugins: [
        new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, /en|ja/)
    ]
}

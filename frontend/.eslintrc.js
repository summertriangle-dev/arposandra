module.exports = {
    env: {
        browser: true,
        es6: true
    },
    extends: [
        "eslint:recommended",
        "plugin:react/recommended"
    ],
    parser: "babel-eslint",
    parserOptions: {
        "ecmaVersion": 2018,
        "sourceType": "module",
    },
    rules: {
        indent: [
            "error",
            4
        ],
        "linebreak-style": [
            "error",
            "unix"
        ],
        quotes: [
            "error",
            "double"
        ],
        semi: [
            "error",
            "never"
        ],
        "max-len": [
            "error", 120, {
                ignoreUrls: true,
                ignoreComments: true,
            }
        ],
        "react/prop-types": [
            "off",
        ]
    },
    overrides: [{
        files: ["webpack.*.js"],
        env: {
            node: true,
            commonjs: true
        },
    }],
    plugins: [
        "babel", "react"
    ],
    settings: {
        react: {
            pragma: "React",
            version: "detect",
        },
        propWrapperFunctions: [
            "forbidExtraProps",
            {"property": "freeze", "object": "Object"},
        ],
    }
}
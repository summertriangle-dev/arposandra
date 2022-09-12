# Config

This file lists the environment variables you can use to configure the app.

## Skyfarer only

AS_ASSET_ADDR: Interface address for the asset server.

AS_ASSET_PORT: Port for the asset server.

## Captain only

AS_WEB_ADDR: Interface address for the web server.

AS_WEB_PORT: Port for the web server.

AS_GIT_REVISION: Displays in the footer. This is normally set with the AS_GIT_REVISION docker build arg.

AS_HOST_ID: Displays in the footer. Otherwise functionally meaningless.

AS_POSTGRES_DSN: Connection string for Postgres server. Something like `postgres://postgres:example@arposandra_db_1/postgres`.

AS_TLINJECT_SECRET: Used to validate TLInject strings. Unlike AS_ASSET_JIT_SECRET, it is not restricted to hex characters.

## Both

AS_DATA_ROOT: Path to your astool data directory. It should look something like this:
```
$AS_DATA_ROOT
- [rgn1...]
  - astool_store.json
  - masters/
    - [abcdef123...]/
  - cache/
    - [pkg...]/
```

Each astool_store.json must contain at minimum the following content:
```
{"latest_complete_master": "<name of a directory under masters/>"}
```

AS_DEV: 0 or 1, specifies whether tornado's debug/autoreload mode is enabled. Also controls whether to load JS from static or webpack-dev-server on localhost:5002.

AS_ASSET_JIT_SECRET: Hex string, case insensitive. The HMAC key to use for generating asset URLs. This must be the same on both Captain and Skyfarer configs, or else images will not load properly.

ASTOOL_STORAGE: Should be set to the same path as AS_DATA_ROOT. Used by astool itself.

AS_CANONICAL_REGION: A string in the format [astool_region_id]:[language_code] (e.g. `"jp:ja"`) that defines the canonical data source for the server.

AS_EXTRA_DICTIONARIES: A list of tuples in the format [astool_region_id]:[language_code]:[alternative_name], separated by ";" (e.g. `"en:en:English (Official);en:zh-TW:Traditional Chinese (Official)"`). It defines the alternative dictionaries the server can use. Note that the last field may contains spaces and also colons; they don't have to be escaped.

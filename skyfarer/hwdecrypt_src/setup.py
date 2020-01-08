from setuptools import setup, Extension

setup(
    name="hwdecrypt",
    version="1.0.0",
    description="An extension module for decrypting ICE data.",
    ext_modules=[
        Extension(
            "hwdecrypt", sources=["hwdecrypt_module.c", "hwd_tool.c"], py_limited_api=True
        )
    ],
)

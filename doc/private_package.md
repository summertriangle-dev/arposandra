# The Private Package

You can use the captain/private/ package to customize your installation. It gets
imported after all core endpoints, so you can stick an `import yourpackage`
in `captain/private/__init__.py` and register your custom handlers there. See
`captain/private/sample` for a working example.
# TODO's

- [ ] read possible Plone version from PyPi in backend_addon / zope-setup
- [ ] extract the instance out into it's own template. Use it to create a single instance, with all features we currently have in zope-setup's instances: single instance, zeo server, client instances for ZEO and RelStorage. This template should bea able to create a ZEO server in the setup, a zeo client (instance1, instance2 aso), as well as single direct storage instance and relstorage clients (instance1, instance2 aso with relstorage backend).
- [ ] provide a docker compose setup and .devcontainer setup in zope-setup and backend_addon




## Goals

- [ ] the combination of zope-setup and backend_addon should be useful to create the same file structure as cookieplone does:
        backend  # backend_addon with a build-in zope setup
        frontend  # volto frontend
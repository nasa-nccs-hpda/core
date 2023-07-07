# Innovation Lab's Core Applications

## Release 2.3.0 (2023-07-07)

### <b> Release Highlights </b>

- Added NotebookImageHelper (see PR https://github.com/nasa-nccs-hpda/core/pull/10 for info)
- Made default executable shell for SystemCommand `/bin/bash`


Still important:

## <b>Celery and Redis Use</b>


ILProcessController and CeleryConfiguration have been updated to allow for multiple celery-enabled applications to run in parallel on the same node. This requires a different method in invoking the application's container as an instance.


To start the container instance:

```
$ singularity instance start -B <drives-to-mount> /path/to/container.sif <instance-name>
INFO: instance started successfully
```

To shell,exec,run with the container instance:

```
$ singularity <shell/exec/run> instance://<instance-name>
```

To stop the container instance (run outside of container if shelled in):

```
$ singularity instance stop <instance-name>
```


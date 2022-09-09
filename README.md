# Innovation Lab's Core Applications

## Release 2.1.0 (2022-07-08)

### <b> Release Highlights </b>

- Refactored Celery and Redis controllers to become non-blocking
- GeospatialImageFile improvements
- Improved DgFile support
- Improved FootprintsQuery


GeospatialImageFile/ImageFile improvement notes:

If you are using GeospatialImageFile and/or ImageFile, the order of the arguments have changes. This may result in some applications getting errors due to an argument being in the wrong position on invocation. Use keyword args compared to positional arguments in case these orders change again. 

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


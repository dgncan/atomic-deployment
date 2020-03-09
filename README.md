# Atomic Deployment Tool
## Configuration
- save ini file as env/test.ini
    Example ini file:
    ```
    [deploy]
    PROJECT_NAME = example-project
    HOST = root@your-host.com
    PEM_FILE = /Users/dogancan/newone.pem

    FILE_OWNER = www.www

    DEPLOY_ROOT_PATH = /home/testroot
    FILE_LIST = composer.lock conf public src vendor
    SHARED_DIRS = runtime uploads
    ```
- if you specify the composer.lock file in FILE_LIST, it will optimization vendor directory (optional for php projects)
  
## Quick Start and Test 
```
./test-deploy.sh dep test
```

## Usage
```
python deploy.py dep test
```

## Todo
- Cleaning up old release after a release

## Credits
This project was inspired by [Deployer](<https://deployer.org/>)
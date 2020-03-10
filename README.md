# Atomic Deployment Tool
  
## Quick Start and Test 
- Remote Server
  ```
  ./test-deploy.sh dep test
  ```
- Local  
  ```
  ./test-deploy.sh dep local
  ```
## Configuration
- For remote, save ini file as env/test.ini
    Example ini file:
    ```
    [deploy]
    PROJECT_NAME = example-project
    HOST = root@your-host.com
    PRIVATE_KEY = /Users/dogancan/newone.pem

    FILE_OWNER = www:www

    DEPLOY_ROOT_PATH = /home/testroot
    FILE_LIST = composer.lock conf public src vendor
    SHARED_DIRS = runtime uploads
    ```
- For Local, save ini file as env/local.ini
    Example ini file:
    ```
    [deploy]
    PROJECT_NAME = example-project
    HOST = 
    PRIVATE_KEY = 

    FILE_OWNER = dogancan:staff

    DEPLOY_ROOT_PATH = ../test_server_root
    FILE_LIST = composer.lock conf public src vendor
    SHARED_DIRS = runtime uploads
    ```    
- if you specify the composer.lock file in FILE_LIST, it will optimize vendor directory (optional for php projects)


## Usage
```
python deploy.py dep test
```

## Steps
- Step 1: Check atomic build path
- Step 2: Create `.dep` directory and `releases` file
- Step 3: Get last build no
- Step 4: Remove and create dist directory
- Step 5: Copying dirs/files in `dist` directory
- Step 6: Copying `settings-local.ini` from `env` directory
- Step 7: Check last active `release` symlink
- Step 8: Check release build no
- Step 9: Checksum for `composer.lock`
- Step 10: Save Release Time and Build to `.dep/releases`
- Step 11: Make build dir and shared dir and set owner
- Step 12: Create symlink `release`
- Step 13: Copy vendor dir from old build
- Step 14: Copy files
- Step 15: Set chown for `release`
- Step 16: `current` link override, check `current` link, unlink release
- Step 17: Make shared dir in project root if not exist
- Step 18: Linked shared directory, make shared sub dir if not exist
- Step 19: Finish Result

## Todo
- Cleaning up old release after a release
- set chown for shared dirs

## Credits
This project was inspired by [Deployer](<https://deployer.org/>)
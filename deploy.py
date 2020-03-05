#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import time
import datetime
import ConfigParser

class Deploy:

    def __init__(self, env):
        self.env = env
        config = ConfigParser.ConfigParser()
        config.read('env/'+self.env+'.ini')

        self.releaseTime = self.get_date(time.time())

        self.PROJECT_NAME = config.get('deploy', 'PROJECT_NAME')
        self.HOST = config.get('deploy', 'HOST')
        self.PEM_FILE = config.get('deploy', 'PEM_FILE')

        self.FILE_OWNER = config.get('deploy', 'FILE_OWNER')
        self.DEPLOY_ROOT_PATH = config.get('deploy', 'DEPLOY_ROOT_PATH')

        self.FILE_LIST = config.get('deploy', 'FILE_LIST')

        self.DEPLOY_PATH = self.DEPLOY_ROOT_PATH+"/"+self.PROJECT_NAME
        self.SHARED_DIRS = config.get('deploy', 'SHARED_DIRS')

        self.remoteCommandPrefix = "ssh -i "+self.PEM_FILE+" "+self.HOST+" "

    def get_date(self, unixtime, format = '%Y%m%d%H%M%S'):
        d = datetime.datetime.fromtimestamp(unixtime)
        return d.strftime(format)

    def run_command(self, cmd):
        output,error = subprocess.Popen(cmd, shell=True, executable="/bin/sh", stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if error:
            print ("Error:"+error)
            exit(1)
        return output

    def run(self):
        remoteCommandPrefix = self.remoteCommandPrefix

        print ('Step 1: Generate buildNo')
        # önce kontrol etmek lazım varmı böyle .dep/releases dosya diye.
        remoteCommand = "tail -1 "+self.DEPLOY_PATH+"/.dep/releases"
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        lastBuildTime, lastBuildNo = result.split(",")
        print ('lastBuildTime:'+lastBuildTime)
        lastBuildNo = int(lastBuildNo)
        buildNo = lastBuildNo+1
        self.buildNo = str(buildNo)
        print (' OK')

        print ('Step 2: Remove dist directory')
        result = self.run_command("rm -rf dist")
        print (' OK')

        print ('Step 3: Make dist directory')
        result = self.run_command("mkdir -p dist")
        print (' OK')

        print ('Step 3: Copying dirs in dist directory')
        result = self.run_command("cp -r "+self.FILE_LIST+" dist/")
        print (' OK')

        print ('Step 4: Save Release Time and Build to .dep/releases')
        remoteCommand = "'echo \""+self.releaseTime+","+self.buildNo+"\" >> "+self.DEPLOY_PATH+"/.dep/releases'"
        print (remoteCommandPrefix + remoteCommand)
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        # output,error = subprocess.Popen(remoteCommandPrefix+remoteCommand, shell=True, executable="/bin/bash", stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        print (result)
        print (' OK')

        print ('Step 5: Check release buildNo')
        remoteCommand = "test -e "+self.DEPLOY_PATH+"/releases/"+self.buildNo+" && echo 1 || echo 0"
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        isExistBuild = result[0].split('\n')[0]
        print (' remote command:'+remoteCommand+' result:'+isExistBuild)

        remoteCommand = "test -e "+self.DEPLOY_PATH+"/release && echo 1 || echo 0"
        result = self.run_command(remoteCommandPrefix + remoteCommand)

        isExistReleaseSymlink = result[0].split('\n')[0]
        print (' remote command:'+remoteCommand+' result:'+isExistReleaseSymlink)
        print("  isExistBuild:", isExistBuild, "isExistReleaseSymlink:",isExistReleaseSymlink)
        print (' OK')

        if isExistBuild == '0':
            print ('Step 6: Make build dir and set owner')
            remoteCommand = " mkdir "+self.DEPLOY_PATH+"/releases/"+self.buildNo
            print (remoteCommandPrefix, remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)

            remoteCommand = "chown -R "+self.FILE_OWNER+" "+self.DEPLOY_PATH+"/releases/"+self.buildNo
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            print (' OK')
        if isExistReleaseSymlink == '0':
            print ('Step 7: create symlink release')
            remoteCommand = "ln -s releases/"+self.buildNo+" "+self.DEPLOY_PATH+"/release"
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            print (' OK')

        print ('Step 7: Copy files')
        command = "rsync -rvlz -e 'ssh -i "+self.PEM_FILE+"' ./dist/*  "+self.HOST+":"+self.DEPLOY_PATH+"/releases/"+self.buildNo+"/"
        result = self.run_command(command)
        print (result)
        print (' OK')

        print ('Step 8: set chown for release')
        remoteCommand = "chown -R icerik.www "+self.DEPLOY_PATH+"/releases/"+self.buildNo
        result = self.run_command(remoteCommandPrefix + remoteCommand)            
        print (result)
        print (' OK')

        print ('Step 9: current link override, check current link, unlink release')
        remoteCommand = "ln -sfT releases/"+self.buildNo+" "+self.DEPLOY_PATH+"/current"
        result = self.run_command(remoteCommandPrefix + remoteCommand)

        remoteCommand = "test -e "+self.DEPLOY_PATH+"/current && echo 1 || echo 0"
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        isCreateNewCurrent = result[0].split('\n')[0]
        if isCreateNewCurrent == '0':
            print ('new current link problem, !!!')
            exit(1)
        print (' OK')

        print ('Step 10: Make shared dir in project root if not exist')
        remoteCommand = "test -e "+self.DEPLOY_PATH+"/shared && echo 1 || echo 0"
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        isExistSharedDir = result[0].split('\n')[0]
        if isExistSharedDir == 0:
            remoteCommand = " mkdir "+self.DEPLOY_PATH+"/shared"
            print (remoteCommandPrefix, remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)
        print (' OK')

        print ('Step 11: linked shared directory')
        for sharedDir in self.SHARED_DIRS.split(" "):
            print ('Step 11.1: Make shared sub dir if not exist')
            remoteCommand = "test -e "+self.DEPLOY_PATH+"/shared/"+sharedDir+" && echo 1 || echo 0"
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            isExistSharedSubDir = result[0].split('\n')[0]
            if isExistSharedSubDir == 0:
                remoteCommand = " mkdir "+self.DEPLOY_PATH+"/shared/"+sharedDir
                print (remoteCommandPrefix, remoteCommand)
                result = self.run_command(remoteCommandPrefix + remoteCommand)
            print (' OK')

            print ('Step 11.2: linked')
            remoteCommand = "ln -sfT ../../shared/"+sharedDir+" "+self.DEPLOY_PATH+"/releases/"+self.buildNo+"/"+sharedDir
            print (remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            print (' OK')

        remoteCommand = "unlink "+self.DEPLOY_PATH+"/release"
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        print
        exit(1)

    def rollback(self, buildNo):
        remoteCommandPrefix = self.remoteCommandPrefix

        print ('Hedeflenen Build No:'+buildNo)
        remoteCommand = "ln -sfT releases/"+buildNo+" "+self.DEPLOY_PATH+"/current"
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        remoteCommand = "test -e "+self.DEPLOY_PATH+"/current && echo 1 || echo 0"
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        isCreateNewCurrent = result[0].split('\n')[0]
        if isCreateNewCurrent == '0':
            print ('yeni current symlink olusamamıs, !!!')
            exit(1)
        remoteCommand = "unlink "+self.DEPLOY_PATH+"/release"
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        print
        exit(1)

    def test(self):
        print (sys.argv)
        print ('test.......')
        
if __name__ == '__main__':
    print ('Deploy.py v.0.1 \n'
            'Doğan Can <dgncan@gmail.com> \n'
            '\n'
            'Atomic Deployment Tool\n'
            '\n'
            'Usage:\n'
            '   python deploy.php [env] [command] [buildno]\n'
            '\n'
            'Available commands:\n'
            '   dep         deploying th project\n'
            '   rollback    rollbacking the specific version of project \n'
            '\n'
            'Example: \n'
            '   python deploy.py test dep 123 \n'
            '   python deploy.py test rollback 11 \n'
            )

    if len(sys.argv) <=2:
        print ('Please input environment and subcommand!\n')
        exit(1)
    
    if len(sys.argv) >2:
        deploy = Deploy(sys.argv[1])
        if sys.argv[2]=='dep':
            deploy.run()
        if sys.argv[2]=='rollback':
            if len(sys.argv) <=3:
                print ('Please input build arguments!\n')
                exit(1)
            deploy.rollback(sys.argv[3])
        if sys.argv[2]=='test':
            deploy.test()

    exit(1)

    print
    print ('Release Time:', deploy.releaseTime)
    print ('Release No:', deploy.buildNo)
    print ('Pem File:', deploy.PEM_FILE)
    print ('Deploy Path:', deploy.DEPLOY_PATH)
    print
   
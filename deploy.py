#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import time
import datetime
import ConfigParser
import shutil

class Cwrite:
    GREY = '\033[90m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m' 

    @staticmethod
    def info(msg):
        print (Cwrite.GREY + msg + Cwrite.ENDC)
    @staticmethod
    def warning(msg):
        print (Cwrite.YELLOW + msg + Cwrite.ENDC)
    @staticmethod
    def error(msg):
        print (Cwrite.RED + msg + Cwrite.ENDC)
    @staticmethod
    def success(msg):
        print (Cwrite.GREEN + msg + Cwrite.ENDC)

class Deploy:

    def __init__(self, env):
        self.env = env
        try:
            config = ConfigParser.ConfigParser()
            config.read('env/'+self.env+'.ini')
            config.get('deploy', 'PROJECT_NAME')

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
        except :
            Cwrite().error('Error:' + str(sys.exc_info()[1]))

    def get_date(self, unixtime, format = '%Y%m%d%H%M%S'):
        d = datetime.datetime.fromtimestamp(unixtime)
        return d.strftime(format)

    def run_command(self, cmd):
        output,error = subprocess.Popen(cmd, shell=True, executable="/bin/sh", stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if error:
            Cwrite().error('Error:' + error)
            exit(1)
        return output

    def run(self):
        cw = Cwrite()
        remoteCommandPrefix = self.remoteCommandPrefix

        cw.warning('Step 1: Check atomic build path')
        remoteCommand = '[ -f "'+self.DEPLOY_PATH+'/.dep/releases" ] && echo 1 || echo 0'
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        cw.info(' '+remoteCommandPrefix + remoteCommand)
        isExistReleases = bool(int(result.split('\n')[0]))
        cw.info(' isExistReleases:'+str(isExistReleases))

        cw.warning('Step 2: Create .dep dir and releases file')
        if isExistReleases == False:
            remoteCommand = '"cd '+self.DEPLOY_PATH+' && mkdir .dep && cd .dep && touch releases"'
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            cw.success(' OK')
        else:
            cw.success(' PASS')   

        cw.warning('Step 3: Remove and Create dist directory')
        if os.path.isdir("dist"):
            shutil.rmtree("dist")
        os.mkdir("dist")
        cw.success(' OK')
        
        cw.warning('Step 4: Copying dirs in dist directory')
        for directory in self.FILE_LIST.split(" "):
            if os.path.isdir(directory):
                result = self.run_command("cp -r "+directory+" dist/")
            cw.info(' Directory: '+directory+' OK')
        cw.success(' OK')

        cw.warning('Step 5: Copying settings-local.ini from env directory')
        os.mkdir("dist/conf")
        shutil.copyfile("env/"+self.env+".ini", "dist/conf/settings-local.ini")
        cw.success(' OK')

        buildNo = 0 

        cw.warning('Step 6: Check last active release symlink')
        remoteCommand = '[ -e "'+self.DEPLOY_PATH+'/release" ] && echo 1 || echo 0'
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        isExistReleaseSymlink = bool(int(result.split('\n')[0]))
        cw.info(' isExistReleaseSymlink:'+str(isExistReleaseSymlink))
        if isExistReleaseSymlink:
            remoteCommand = "readlink "+self.DEPLOY_PATH+"/release"
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            path = result.split('\n')[0].split("/")
            buildNo = int(path[len(path)-1])
            cw.info(" Active Release :"+str(buildNo))
            cw.success(' OK')
        else:
            cw.success(' PASS')


        cw.warning('Step 7: Last buildNo and Time by .dep/releases')
        if buildNo == 0:
            remoteCommand = "tail -1 "+self.DEPLOY_PATH+"/.dep/releases"
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            if len(result) != 0:
                lastBuildTime, lastBuildNo = result.split(",")
                lastBuildNo = int(lastBuildNo)
                cw.info(' Last build No:'+str(lastBuildNo)+' - Date Time:'+lastBuildTime)
                buildNo = lastBuildNo+1
                cw.success(' OK')
            else:
                buildNo = 1
                cw.success(' OK')
        else:
            cw.success(' PASS')
    
        self.buildNo = str(buildNo)

        cw.info(' New build No:'+self.buildNo+' - Date Time:'+self.releaseTime)
        cw.success(' OK')

        cw.warning('Step 8: Check release buildNo')
        remoteCommand = '[ -e "'+self.DEPLOY_PATH+'/releases/'+self.buildNo+'" ] && echo 1 || echo 0'
        cw.info(' '+remoteCommandPrefix + remoteCommand)
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        isExistBuild = bool(int(result.split('\n')[0]))

        cw.info(' isExistReleaseSymlink:'+str(isExistReleaseSymlink))
        cw.info(' isExistBuild:'+str(isExistBuild))

        cw.warning('Step 9: Save Release Time and Build to .dep/releases')
        remoteCommand = "'echo \""+self.releaseTime+","+self.buildNo+"\" >> "+self.DEPLOY_PATH+"/.dep/releases'"
        cw.info(' '+remoteCommandPrefix + remoteCommand)
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        cw.info(' '+result)
        cw.success(' OK')


        cw.warning('Step 10: Make build dir and shared dir and set owner')
        if isExistBuild == False:
            remoteCommand = " mkdir -p "+self.DEPLOY_PATH+"/releases/"+self.buildNo
            cw.info(' '+remoteCommandPrefix + remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)

            remoteCommand = "chown -R "+self.FILE_OWNER+" "+self.DEPLOY_PATH+"/releases/"+self.buildNo
            cw.info(' '+remoteCommandPrefix + remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            cw.success(' OK')
        else:
            cw.info(' the build dir is exist.')
            cw.success(' PASS')

        cw.warning('Step 11: create symlink release')
        if isExistReleaseSymlink == False:
            remoteCommand = "ln -s releases/"+self.buildNo+" "+self.DEPLOY_PATH+"/release"
            cw.info(' '+remoteCommandPrefix + remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            cw.success(' OK')
        else:
            cw.info(' the build dir symlink is exist.')
            cw.success(' PASS')


        cw.warning('Step 12: Copy files')
        command = "rsync -rvlz -e 'ssh -i "+self.PEM_FILE+"' ./dist/*  "+self.HOST+":"+self.DEPLOY_PATH+"/releases/"+self.buildNo+"/"
        cw.info(' '+command)
        result = self.run_command(command)
        cw.info(' '+result)
        cw.success(' OK')

        cw.warning('Step 13: set chown for release')
        remoteCommand = "chown -R icerik.www "+self.DEPLOY_PATH+"/releases/"+self.buildNo
        cw.info(' '+remoteCommandPrefix + remoteCommand)
        result = self.run_command(remoteCommandPrefix + remoteCommand)            
        cw.info(' '+result)
        cw.success(' OK')

        cw.warning('Step 14: current link override, check current link, unlink release')
        remoteCommand = "ln -sfT releases/"+self.buildNo+" "+self.DEPLOY_PATH+"/current"
        cw.info(' '+remoteCommandPrefix + remoteCommand)
        result = self.run_command(remoteCommandPrefix + remoteCommand)

        remoteCommand = '[ -e "'+self.DEPLOY_PATH+'/current" ] && echo 1 || echo 0'
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        cw.info(' '+remoteCommandPrefix + remoteCommand)
        isCreateNewCurrent = bool(int(result.split('\n')[0]))
        cw.info(' isCreateNewCurrent:' + str(isCreateNewCurrent))
        if isCreateNewCurrent == False:
            cw.error(' New current link problem!')
            exit(1)
        cw.success(' OK')

        cw.warning('Step 15: Make shared dir in project root if not exist')
        remoteCommand = '[ -e "'+self.DEPLOY_PATH+'/shared" ] && echo 1 || echo 0'
        cw.info(' ' + remoteCommandPrefix + remoteCommand)
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        isExistSharedDir = bool(int(result.split('\n')[0]))
        cw.info(' isExistSharedDir:' + str(isExistSharedDir))
        if isExistSharedDir == 0:
            remoteCommand = " mkdir "+self.DEPLOY_PATH+"/shared"
            cw.info(' ' + remoteCommandPrefix + remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            cw.success(' OK')
        else:
            cw.success(' PASS')

        cw.warning('Step 16: linked shared directory, make shared sub dir if not exist')
        for sharedDir in self.SHARED_DIRS.split(" "):
            remoteCommand = '[ -e "'+self.DEPLOY_PATH+'/shared/'+sharedDir+'" ] && echo 1 || echo 0'
            cw.info(' ' + remoteCommandPrefix + remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            isExistSharedSubDir = bool(int(result.split('\n')[0]))
            cw.info(' isExistSharedSubDir:' + str(isExistSharedSubDir))
            if isExistSharedSubDir == False:
                remoteCommand = " mkdir "+self.DEPLOY_PATH+"/shared/"+sharedDir
                cw.info(' ' + remoteCommandPrefix + remoteCommand)
                result = self.run_command(remoteCommandPrefix + remoteCommand)
                cw.success(' OK')

            remoteCommand = "ln -sfT ../../shared/"+sharedDir+" "+self.DEPLOY_PATH+"/releases/"+self.buildNo+"/"+sharedDir
            cw.info(' ' + remoteCommandPrefix + remoteCommand)
            result = self.run_command(remoteCommandPrefix + remoteCommand)
            cw.success(' OK')

        remoteCommand = "unlink "+self.DEPLOY_PATH+"/release"
        cw.info(' ' + remoteCommandPrefix + remoteCommand)
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        cw.success(' OK')
        cw.success(' FINISH')
        exit(1)

    def rollback(self, buildNo):
        cw = Cwrite()
        remoteCommandPrefix = self.remoteCommandPrefix

        cw.warning('Hedeflenen Build No:'+buildNo)
        remoteCommand = "ln -sfT releases/"+buildNo+" "+self.DEPLOY_PATH+"/current"
        cw.info(' ' + remoteCommandPrefix + remoteCommand)
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        remoteCommand = '[ -e "'+self.DEPLOY_PATH+'/current" ] && echo 1 || echo 0'
        result = self.run_command(remoteCommandPrefix + remoteCommand)
        isCreateNewCurrent = bool(int(result.split('\n')[0]))
        if isCreateNewCurrent == False:
            cw.error (' New current symlink can not created!')
            exit(1)
        remoteCommand = "unlink "+self.DEPLOY_PATH+"/release"
        result = self.run_command(remoteCommandPrefix + remoteCommand)

        cw.success(' FINISH')
        exit(1)

    def test(self):
        print (sys.argv)
        print ('test.......')

def intro():
    cw = Cwrite()
    cw.success('Deploy.py v.0.1 \n'
            ' Doğan Can <dgncan@gmail.com> \n'
            '\n'
            ' Atomic Deployment Tool\n'
            '====================================\n'
            ) 
def help():
    cw = Cwrite()
    cw.info('Usage:\n'
            '   python deploy.php [command] [env] [buildno]\n'
            '\n'
            'Available commands:\n'
            '   dep         deploying th project\n'
            '   rollback    rollbacking the specific version of project \n'
            '\n'
            'Example: \n'
            '   python deploy.py dep test\n'
            '   python deploy.py rollback test 92 \n'
            )
if __name__ == '__main__':
    intro()
    if len(sys.argv) <=2:
        help()
        Cwrite().warning('Please input environment and subcommand!\n')
        exit(1)
    
    if len(sys.argv) >2:
        deploy = Deploy(sys.argv[2])
        if sys.argv[1]=='dep':
            deploy.run()
        if sys.argv[1]=='rollback':
            if len(sys.argv) <=3:
                print ('Please input build arguments!\n')
                exit(1)
            deploy.rollback(sys.argv[3])
        if sys.argv[1]=='test':
            deploy.test()

    exit(1)

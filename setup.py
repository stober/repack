'''
@author: stober
'''

#from setuptools import setup
from distutils.core import setup
import sys
import re
import os
import shutil
import ConfigParser
import argparse

def create_directories(name):
    pkgdir = os.path.dirname(os.path.abspath(__file__)) + "/" + name
    try:
        os.mkdir(pkgdir)
        os.mkdir(pkgdir + "/repos")
        os.mkdir(pkgdir + "/subs")
        open(pkgdir + "/subs/__init__.py","w").close() # touch
    except OSError:
        print "Directories already exists. Run with --delete to remove."
        
def delete_project(name):
    pkgdir = os.path.dirname(os.path.abspath(__file__)) + "/" + name
    if raw_input('Really delete project %s? (y/N) ' % name) == 'y':
        shutil.rmtree(pkgdir)

def clone_gitrepos(name, gitrepos):
    pkgdir = os.path.dirname(os.path.abspath(__file__)) + "/" + name + "/repos/"
    for package,url in gitrepos:
        os.system("git clone %s %s" % (url, pkgdir + package))

def build_subpackages(name,subpackages):
    orgdir = os.getcwd()
    pkgdir = os.path.dirname(os.path.abspath(__file__)) + "/" + name 
    
    for package in subpackages:
        repo = pkgdir + "/repos/" + package
        os.chdir(repo)
        sub = pkgdir + "/subs/"
        os.system("python setup.py install --install-lib " + sub)

    os.chdir(orgdir)

def subs(line,namespace,subpackages):
    for package in subpackages:
        # these are relatively brittle regular expressions - an alternative approach may require modifying the import statement with import hooks
        line = re.sub("\Afrom %s import" % package , "from %s.%s import" % (namespace,package), line)
        line = re.sub("\Aimport %s" % package, "import %s.%s" % (namespace,package), line)
    return line
        
def rename_subpackages(namespace,subpackages):
    """
    Munges import statements that point to other subpackages in the new package namespace.
    """
    pkgdir = os.path.dirname(os.path.abspath(__file__)) + "/" + namespace + "/subs/"
    print pkgdir
    for root, dirs, files in os.walk(pkgdir):
        for f in files:
            if os.path.splitext(f)[1] == '.py':
                # read in file
                fp = open('%s/%s' % (root,f))
                lines = fp.readlines()
                fp.close()

                # munge imports and write
                fp = open('%s/%s' % (root,f),"w")
                for line in lines:
                    fp.write(subs(line,namespace,subpackages))
                fp.close()


def main():
    parser = argparse.ArgumentParser(description='Repack some Python modules.')
    parser.add_argument('--init', action='store_true',default=False,help='Initialize the necessary directories for a project.')
    parser.add_argument('--config',nargs=1,help='The config file for the new package.')
    parser.add_argument('--debug',action='store_true',default=False,help='Print debug information.')
    parser.add_argument('--delete',action='store_true',default=False,help='Delete package directory.')
    parser.add_argument('--clone',action='store_true',default=False,help='Clone repositories of submodules.')
    parser.add_argument('--setup',action='store_true',default=False,help='Run setup for package.')
    parser.add_argument('--build',action='store_true',default=False,help='Build submodules.')
    parser.add_argument('--distutils',action='store_true',default=False,help='Run distutils.')
    parser.add_argument('distutil_args',nargs='*',help='Arguments for distutils.')
    args = parser.parse_args()
    debug = args.debug

    # read config file
    config = ConfigParser.ConfigParser()
    config.read(args.config)
    namespace = config.sections()[0]
    gitrepos = config.items(namespace)
    subpackages = [item[0] for item in gitrepos]
    scoped_packages = ["%s.%s" % (namespace, package) for package in subpackages]

    if args.init:
        create_directories(namespace)
    elif args.delete:
        delete_project(namespace)
    elif args.clone:
        clone_gitrepos(namespace,gitrepos)
    elif args.build:
        build_subpackages(namespace,subpackages)
        rename_subpackages(namespace,subpackages)
    elif args.distutils:
        setup_data = dict(config.items('setup'))
        sys.argv = [sys.argv[0]] + args.distutil_args
        
        setup(name=namespace,
              version=setup_data['version'],
              description='',
              author=setup_data['author'],
              author_email=setup_data['author_email'],
              package_dir={namespace:namespace + '/subs'},
              packages=scoped_packages
              )

if __name__ == '__main__':
    main()
    
      

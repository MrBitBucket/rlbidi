from setuptools import setup, Extension, find_packages
import sys, os, subprocess, shutil, glob

pjoin=os.path.join
dirname=os.path.dirname
normpath = os.path.normpath
isfile = os.path.isfile
isdir = os.path.isdir
verbose=int(os.environ.get("SETUP_VERBOSE","0"))
limited_abi = int(os.environ.get('LIMITED_ABI','38'))
cibuildwheel = os.environ.get('CIBUILDWHEEL','')=='1'

def lineList(L):
    return '\n     '+('\n     '.join((repr(_) for _ in L)))

def lineListDir(d):
    return lineList(os.listdir(d))

def cat(fn):
    with open(fn,'r') as _:
        return _.read()

def sprun(args):
    if verbose:
        print(f'##### about to execute\n  {" ".join(args)}')
    try:
        subprocess.run(args)
    except:
        t,e,b = sys.exc_info()
        print(f'!!!!! {args[0]} raised {e}')
        raise

options = {}
ext_modules = []
data_files = []
setup_py = sys.argv[0]=='setup.py'
rlbidi_src = 'src'
_rlbidi_c = pjoin(rlbidi_src,'_rlbidi.c')
bfDir = 'build'
forceHelp = setup_py and 'bdist_wheel' in sys.argv[1:]
if forceHelp:
    print('''!!!!! setup.py bdist_wheel will not work !!!!!\n''')
if forceHelp or (setup_py and 'help' in sys.argv):
    print('''
    python setup.py clean remove fribidi-src, build & dist
    python setup.py help  to give this help
    python setup.py sdist to make a source distro
    pip wheel -w dist . [-v] to make a wheel
    pip install --editable . to install for developing
    python setup.py test to run tests
''')
    sys.exit(-1 if forceHelp else 0)
elif setup_py and 'clean' in sys.argv:
    for d in 'fribidi-src dist build'.split():
        if isdir(d):
            if verbose: print(f'##### shutil.rmtree({d!r})')
            shutil.rmtree(d)
    sys.exit(0)
elif setup_py and 'test' in sys.argv:
    sprun((sys.executable,pjoin('test','test_rlbidi.py')))
    sys.exit(0)
elif setup_py and 'sdist' in sys.argv:
    data_files = [_rlbidi_c]
else:
    #+++++++++++++++++++++++++ start limited C api support
    def make_la_info():
        '''compute limited api and abi info'''
        from pathlib import Path
        Path(_rlbidi_c).touch()
        try:
            from setuptools.command.bdist_wheel import get_abi_tag
        except ImportError:
            try:
                from wheel.bdist_wheel import get_abi_tag
            except ImportError:
                from wheel._bdist_wheel import get_abi_tag
        global cpstr, limited_define_macros
        cpstr = get_abi_tag()
        if cpstr.startswith("cp"):
            lav = '0x03080000'
            cpstr = f'cp{limited_abi}'
            #if sys.platform == "darwin":
            #   machine = sysconfig.get_platform().split('-')[-1]
            #   if machine=='arm64' or os.environ.get('ARCHFLAGS','')=='-arch arm64':
            #       #according to cibuildwheel/github M1 supports pythons >= 3.8
            #       lav = '0x03080000'
            #       cpstr = f'cp{max(limited_abi,38)}'
            limited_define_macros=[("Py_LIMITED_API", lav)]

    make_la_info()
    options = {'bdist_wheel': {'py_limited_api': cpstr}}

    #------------------------- end   limited C api support

    def locationValueError(msg):
        print('!!!!! %s\nls(%r)\n%s\n!!!!!''' % (msg,cwd,lineListDir(cwd)))
        raise ValueError(msg)

    def bfName(**kwargs):
        from setuptools.dist import Distribution
        # create a fake distribution from arguments
        dist = Distribution(attrs=kwargs)
        # finalize bdist_wheel command
        bdist_wheel_cmd = dist.get_command_obj('bdist_wheel')
        bdist_wheel_cmd.ensure_finalized()
        # wheel file name
        #distname = bdist_wheel_cmd.wheel_dist_name
        tag = '-'.join(bdist_wheel_cmd.get_tag())
        return f'build-{tag}'

    if cibuildwheel:
        bfDir = bfName(ext_modules=[Extension("",[])], options=options)

    def win_patches():
        config_h = pjoin(fribidi_src,bfDir,'config.h')
        with open(config_h,'r') as _:
            text = _.read()
        if bfDir.endswith('-win32'):
            text = text.replace('#define HAVE_STRINGS_H\n','#undef HAVE_STRINGS_H\n')
            text = text.replace('#define STDC_HEADERS 1','')
        with open(config_h,'w') as _:
            _.write(text)

    def setupFribidiSrc(target, existing=False):
        if not existing:
            from dulwich import porcelain
            refspecs=[b'cfc71cda065db859d8b4f1e3c6fe5da7ab02469a']
            print(f'##### porcelain.clone("https://github.com/fribidi/fribidi,{target},{refspecs=})')
            porcelain.clone("https://github.com/fribidi/fribidi", target, refspecs=refspecs)
        cwd = os.getcwd()
        os.chdir(target)
        try:
            sprun(['meson','setup','-Ddocs=false','--backend=ninja',bfDir,'--wipe'])
            sprun(['ninja','-C',bfDir])
        finally:
            os.chdir(cwd)

    def getFribidiSrc():
        print(f'##### attempting git clone and meson/ninja {bfDir} in {os.getcwd()}')
        try:
            target = 'fribidi-src'
            if os.path.isdir(target):
                if int(os.environ.get('CLEAN_FRIBIDI','0'))>=1:
                    shutil.rmtree(target)
                    print(f'##### removed existing directory {target!r}')
                    setupFribidiSrc(target,existing=True)
                else:
                    print(f'##### using existing directory {target!r}')
                    setupFribidiSrc(target, existing=True)

            else:
                setupFribidiSrc(target)
        except:
            t,e,b = sys.exc_info()
            print(f'!!!!! clone and build commands failed with {e}')
            raise
        else:
            return target

    fribidi_src = getFribidiSrc()
    if bfDir.endswith('-win32'): win_patches()
    if verbose:
        print("##### fribidi_src=%r\n##### rlbidi_src=%r" % (fribidi_src,rlbidi_src))

    meson_lib = pjoin(fribidi_src,bfDir,'lib')
    def getIncludeDirs():
        for _top in (bfDir,None):
            top = pjoin(fribidi_src,_top) if _top else fribidi_src
            lib = pjoin(top,'lib')
            if isfile(pjoin(top,'config.h')) and isfile(pjoin(lib,'fribidi-config.h')):
                I = [top,lib]
                if _top:
                    gen = pjoin(top,'gen.tab')
                    if isfile(pjoin(gen,'fribidi-unicode-version.h')):
                        I.append(gen)
                    return I
        locationValueError(f'''Cannot locate a suitable config.h file.
        meson setup -Ddocs=false --backend=ninja {bfDir} --wipe
        ninja -C {bfDir}
    or
        ./autogen.sh
        ./configure''')
    include_dirs = [_ for _ in (getIncludeDirs() + [pjoin(fribidi_src,"lib"),pjoin(fribidi_src,'gen.tab'),rlbidi_src]) if isdir(_)]
    if verbose:
        print("##### include_dirs=%s" % lineList(include_dirs))
        if verbose>2:
            config_h = pjoin(fribidi_src,bfDir,'config.h')
            if isfile(config_h):
                print(f'##### {config_h} start\n{cat(config_h)}\n##### {config_h} end')
            else:
                print(f'!!!!! {config_h} not found')

    if isdir(meson_lib):
        if sys.platform=='win32':
            if verbose:
                print('##### meson_lib ls(%r)\n%s' % (meson_lib,lineListDir(meson_lib)))
            meson_lib = pjoin(meson_lib,'fribidi.lib')
        else:
            meson_lib = pjoin(meson_lib,'libfribidi.a')

        if not isfile(meson_lib):
            meson_lib = None
    else:
        meson_lib = None


    libraries = []
    if meson_lib:
        extra_objects = [meson_lib]
        lib_sources = []
        if verbose:
            print('##### using static libraries %s' % lineList(libraries))
    else:
        extra_objects = []
        lib_sources = [pjoin(fribidi_src,p) for p in """
                        lib/fribidi.c
                        lib/fribidi-arabic.c
                        lib/fribidi-bidi.c
                        lib/fribidi-bidi-types.c
                        lib/fribidi-brackets.c
                        lib/fribidi-deprecated.c
                        lib/fribidi-joining.c
                        lib/fribidi-joining-types.c
                        lib/fribidi-mirroring.c
                        lib/fribidi-run.c
                        lib/fribidi-shape.c
                        lib/fribidi-char-sets-cp1256.c
                        lib/fribidi-char-sets-iso8859-8.c
                        lib/fribidi-char-sets-cap-rtl.c
                        lib/fribidi-char-sets-utf8.c
                        lib/fribidi-char-sets.c
                        lib/fribidi-char-sets-cp1255.c
                        lib/fribidi-char-sets-iso8859-6.c
                        """.split()]
    ext_modules=[
        Extension(
            name='rlbidi._rlbidi',
            sources=[_rlbidi_c] + lib_sources,
            define_macros=[("HAVE_CONFIG_H", 1)] + limited_define_macros,
            libraries=libraries,
            extra_objects = extra_objects,
            include_dirs=include_dirs,
            py_limited_api=True,
            ),
        ]

def get_version():
    with open(pjoin("src","rlbidi","__init__.py"),"r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('__version__'):
                version = eval(line.split('=')[1].strip(),{})

    if ext_modules:
        with open(pjoin("src","rlbidi_version.h"),'w') as f:
            f.write('#define RLBIDI_VERSION %s\n' % version)

    return version

setup(
    name="rlbidi",
    version=get_version(),
    ext_modules = ext_modules,
    author="Yaacov Zamir, Nir Soffer, Robin Becker",
    author_email="kzamir@walla.co.il",
    description="Python fribidi interface module",
    long_description = open("README.rst").read(),
    license="GPL-2.0-only",
    packages = find_packages("src"),
    package_dir = {'': "src"},
    data_files = data_files,
    extras_require={},
    options = options,
    )


import sys
import re
import textwrap
from doctest import OutputChecker, ELLIPSIS
from tests.test_pip import reset_env, run_pip, write_file, get_env, pyversion
from tests.local_repos import local_checkout, local_repo


distribute_re = re.compile('^distribute==[0-9.]+\n', re.MULTILINE)
latest_version_re = re.compile('^Latest Version: [0-9.]+\n', re.MULTILINE)

def _check_output(result, expected):
    checker = OutputChecker()
    actual = str(result)

    ## FIXME!  The following is a TOTAL hack.  For some reason the
    ## __str__ result for pkg_resources.Requirement gets downcased on
    ## Windows.  Since INITools is the only package we're installing
    ## in this file with funky case requirements, I'm forcibly
    ## upcasing it.  You can also normalize everything to lowercase,
    ## but then you have to remember to upcase <BLANKLINE>.  The right
    ## thing to do in the end is probably to find out how to report
    ## the proper fully-cased package name in our error message.
    if sys.platform == 'win32':
        actual = actual.replace('initools', 'INITools')

    # This allows our existing tests to work when run in a context
    # with distribute installed.
    actual = distribute_re.sub('######', actual)
    
    # Replace the latest version so that the test won't break.
    actual = latest_version_re.sub('', actual)

    def banner(msg):
        return '\n========== %s ==========\n' % msg
    assert checker.check_output(expected, actual, ELLIPSIS), banner('EXPECTED')+expected+banner('ACTUAL')+actual+banner(6*'=')

def test_show():
    env = reset_env()
    write_file('requires.txt', textwrap.dedent("""\
        INITools==0.2
        """))
    result = run_pip('install', '-r', env.scratch_path/'requires.txt')
    result = run_pip('show', 'INITools', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: pip show INITools
        -- stdout: --------------------
        Package:        INITools
        Summary:        Tools for parsing and using INI-style files
        Version:        0.2
        Author:         Ian Bicking
        Homepage:       http://pythonpaste.org/initools/
        License:        MIT
        """)
    _check_output(result, expected)

    
def test_show_with_pypi_package():
    env = reset_env()
    result = run_pip('show', 'pypi', expect_stderr=True)
    expected = textwrap.dedent("""\
        Script result: pip show pypi
        -- stdout: --------------------
        Package:        pypi
        Summary:        PyPI is the Python Package Index at http://pypi.python.org/
        Latest Version: 2005-08-01
        Author:         Richard Jones
        Homepage:       http://wiki.python.org/moin/CheeseShopDev
        License:        UNKNOWN
        """)
    _check_output(result, expected)


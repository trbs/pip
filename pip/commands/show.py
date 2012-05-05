from __future__ import with_statement

import sys
import warnings
import pkg_resources
import pip.download
from pip.basecommand import Command
from pip.backwardcompat import xmlrpclib
from pip.exceptions import ShowError, DistributionNotFound, CommandError
from pip.index import PackageFinder
from pip.req import InstallRequirement

try:
    import pkginfo
    HAS_PKGINFO = True
except ImportError:
    HAS_PKGINFO = False

class ShowCommand(Command):
    name = 'show'
    usage = '%proc PACKAGE_NAME'
    summary = 'Show detailed information about an installed package'

    def __init__(self):
        super(ShowCommand, self).__init__()
        self.parser.add_option(
            '--index',
            dest='index_url',
            metavar='URL',
            default='http://pypi.python.org/pypi',
            help='Base URL of Python Package Index (default %default)')
        self.parser.add_option(
            '--no-index',
            dest='no_index',
            action='store_true',
            default=False,
            help='Ignore package index (only looking at --find-links URLs instead)')

    def installed_package(self, pkg_name, options):
        local_package = None

        for dist in pkg_resources.working_set:
            if pkg_name == dist.project_name:
                local_package = dist
                break

        return local_package

    def installed_summary(self, local_package):
        try:
            pkg_info = local_package.get_metadata("PKG-INFO")
        except IOError:
            pass
        else:
            for line in pkg_info.split("\n"):
                if line.startswith("Summary: "):
                    summary = line.split("Summary: ", 1)[1]
                    return summary
        return

    def run(self, options, args):
        if not args:
            raise CommandError('Missing required argument (package name).')
        if len(args)>1:
            raise CommandError('Too many arguments.')

        pkg_name = args[0]

        project_name = None
        installed_version = None
        latest_version = None
        metadata = None
        summary = None
        requires = None
        
        local_package = self.installed_package(pkg_name, options)     
        if options.no_index and local_package is None:
            raise ShowError('%s is not installed' % arg)

        if local_package:
            project_name = local_package.project_name
            installed_version = local_package.version
            summary = self.installed_summary(local_package)
            requires = local_package.requires()

        if not options.no_index:
            pypi = xmlrpclib.ServerProxy(options.index_url, pip.download.xmlrpclib_transport)
            try:
                latest_version = pypi.package_releases(pkg_name)
                if not latest_version and local_package is None:
                    raise ShowError('%s is not installed and not available on PyPi' % pkg_name)
                latest_version = latest_version[0]
            except IndexError:
                pass
            else:
                metadata = pypi.release_data(pkg_name, latest_version)
                if not project_name:
                    project_name = metadata['name']
                summary = metadata.get('summary', summary)
                requires = metadata.get('requires', requires)
        elif HAS_PKGINFO:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pkg_info = pkginfo.Installed(pkg_name)
                metadata = dict((k,getattr(pkg_info, k)) for k in pkg_info.iterkeys())

        f = sys.stdout

        f.write('Package:        %s\n' % project_name)
        if summary:
            f.write('Summary:        %s\n' % summary)
        if installed_version:
            f.write('Version:        %s\n' % installed_version)
        if latest_version:
            f.write('Latest Version: %s\n' % latest_version)
        if metadata:
            author = metadata.get('author', None)
            docs_url = metadata.get('docs_url', None)
            home_page = metadata.get('home_page', None)
            license = metadata.get('license', None)
            if author:
                f.write('Author:         %s\n' % author)
            if docs_url:
                f.write('Documentation:  %s\n' % home_page)
            if home_page:
                f.write('Homepage:       %s\n' % home_page)
            if license:
                f.write('License:        %s\n' % license)

        if requires:
            f.write('\nRequires:\n')
            for dep in requires:
                f.write("\t%s\n" % dep)

ShowCommand()

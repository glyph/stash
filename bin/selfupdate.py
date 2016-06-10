# coding=utf-8
"""
Selfupdate StaSh from the GitHub repo.

Usage: selfupdate.py [-n] [-f] [branch]

       branch         default to master

       -n, --check    check for update only
       -f, --force    update without checking for new version
"""
import os
import sys
import requests
from random import randint
from argparse import ArgumentParser

_stash = globals()['_stash']

URL_BASE = 'https://raw.githubusercontent.com/{owner}/stash'
DEFAULT_REPO_OWNER="ywangd"


class UpdateError(Exception):
    pass


def get_remote_version(owner, branch):
    """
    Get the version string for the given branch from the remote repo
    :param branch:
    :return:
    """
    import ast

    url = '%s/%s/stash.py?q=%s' % (URL_BASE.format(owner=owner), branch, randint(1, 999999))

    try:
        req = requests.get(url)
        lines = req.text.splitlines()
    except:
        raise UpdateError('Network error')
    else:
        if req.status_code==404:
            raise UpdateError('Repository/branch not found')

    for line in lines:
        if line.startswith('__version__'):
            remote_version = ast.literal_eval(line.split('=')[1].strip())
            return remote_version

    raise UpdateError('Remote version cannot be decided')


def main(args):

    from distutils.version import StrictVersion

    ap = ArgumentParser()
    ap.add_argument('branch', nargs='?', help='the branch to update to')
    ap.add_argument('repository', nargs='?', help='the user owning the target repository to update to')
    ap.add_argument('-n', '--check', action='store_true', help='check for update only')
    ap.add_argument('-f', '--force', action='store_true', help='update without checking for new version')
    ns = ap.parse_args(args)

    if ns.branch is not None:
        SELFUPDATE_BRANCH = ns.branch
    else:
        SELFUPDATE_BRANCH = os.environ.get('SELFUPDATE_BRANCH', 'master')
    
    if ns.repository is not None:
        SELFUPDATE_REPO = ns.repository
    else:
        SELFUPDATE_REPO = os.environ.get('SELFUPDATE_REPOSITORY',DEFAULT_REPO_OWNER)

    print _stash.text_style('Running selfupdate ...',
                            {'color': 'yellow', 'traits': ['bold']})
    print u'%s: %s/%s' % (_stash.text_bold('Branch'), SELFUPDATE_REPO, SELFUPDATE_BRANCH)

    has_update = True
    # Check for update if it is not forced updating
    if not ns.force:
        local_version = globals()['_stash'].__version__
        try:
            print 'Checking for new version ...'
            remote_version = get_remote_version(SELFUPDATE_REPO, SELFUPDATE_BRANCH)

            if StrictVersion(remote_version) > StrictVersion(local_version):
                print 'New version available: %s' % remote_version
            else:
                has_update = False
                print 'Already at latest version'

        except UpdateError as e:
            has_update = False  # do not update in case of errors
            print _stash.text_color('Error: %s' % e.message, 'red')

    # Perform update if new version is available and not just checking only
    if not ns.check and has_update:

        url = '%s/%s/getstash.py' % (URL_BASE.format(owner=SELFUPDATE_REPO), SELFUPDATE_BRANCH)
        print u'%s: %s' % (_stash.text_bold('Url'),
                           _stash.text_style(url, {'color': 'blue', 'traits': ['underline']}))

        try:
            exec requests.get(
                '%s/%s/getstash.py?q=%s' % (URL_BASE.format(owner=SELFUPDATE_REPO),
                                            SELFUPDATE_BRANCH,
                                            randint(1, 999999))
            ).text in {'_IS_UPDATE': True, '_br': SELFUPDATE_BRANCH,'_repo':SELFUPDATE_REPO}
            print _stash.text_color('Update completed.', 'green')
            print _stash.text_color('Please restart Pythonista to ensure changes becoming effective.', 'green')

        except SystemExit:
            print _stash.text_color('Failed to update. Please try again.', 'red')


if __name__ == '__main__':
    main(sys.argv[1:])

from __future__ import with_statement

import unittest


class FunctionalTest(unittest.TestCase):

    def setUp(self):
        from repoze.depinj import clear
        clear()

        import tempfile
        self.tempdir = tempfile.mkdtemp('.karlservetests')

        from repoze.depinj import inject
        from karlserve.instance import KarlPGTextIndex
        inject(DummyTextIndex, KarlPGTextIndex)

    def tearDown(self):
        from repoze.depinj import clear
        clear()

        import shutil
        shutil.rmtree(self.tempdir)

    def make_app(self, ini=None, instances=None):
        import os
        import pkg_resources
        import shutil
        if ini is None:
            ini = karlserve_ini_1
        if instances is None:
            instances = instances_ini_1
        tmp = self.tempdir
        etc = os.path.join(tmp, 'etc')
        os.mkdir(etc)
        inifile = os.path.join(etc, 'karlserve.ini')
        with open(inifile, 'w') as out:
            out.write(ini)
        instancesfile = os.path.join(etc, 'instances.ini')
        with open(instancesfile, 'w') as out:
            out.write(instances % dict(tmp=tmp))
        os.mkdir(os.path.join(tmp, 'var'))
        os.mkdir(os.path.join(tmp, 'mailout'))

        from webtest import TestApp
        from paste.deploy import loadapp
        return TestApp(loadapp('config://%s' % inifile))

    def login_and_make_a_blog_post(self, app, start_href):
        response = app.get(start_href)
        while response.status_int > 300:
            response = response.follow()
        form = response.form
        form['login'] = 'admin'
        form['password'] = 'admin'
        response = form.submit()
        while response.status_int > 300:
            response = response.follow()
        response = response.click('BLOG')
        response = response.click('Add Blog')
        form = response.forms['save']
        form['title'] = 'Test blog entry.'
        form['text'] = 'My very interesting content'
        response = form.submit('submit')
        while response.status_int > 300:
            response = response.follow()
        body = str(response)
        self.assertTrue('Test blog entry.' in body)
        self.assertTrue('My very interesting content' in body)

    def test_test_it(self):
        app = self.make_app()
        self.login_and_make_a_blog_post(app, '/test1')
        self.login_and_make_a_blog_post(app, '/test2')


class DummyTextIndex(object):
    from zope.interface import implements
    from repoze.catalog.interfaces import ICatalogIndex
    implements(ICatalogIndex)

    def __init__(self, discriminator):
        self.discrminator = discriminator

    def index_doc(self, docid, doc):
        pass


karlserve_ini_1 = """[app:karlserve]
use = egg:karlserve#application
instances_config = %(here)s/instances.ini
mail_queue_path = %(here)s/../var/mailout
error_monitor_dir = %(here)s/../var/error
blob_cache = %(here)s/../var/blob-cache
who_secret = secret
who_cookie = choco

[filter:browserid]
use = egg:repoze.browserid#browserid
secret_key = $hbs7h))$1

[pipeline:main]
pipeline =
    browserid
    karlserve

[server:main]
use = egg:Paste#http
host = 0.0.0.0
port = 5678
"""

instances_ini_1 = """
[instance:test1]
zodb_uri = file://%(tmp)s/var/test1.db

[instance:test2]
zodb_uri = file://%(tmp)s/var/test2.db
pgtextindex.dsn = ho ho ho
"""


# -*- coding: utf-8 -*-

import os
from unittest import mock

import nikola
import nikola.plugins.command.import_wordpress
from nikola.plugins.command.import_wordpress import (
    modernize_qtranslate_tags, separate_qtranslate_tagged_langs)
from .base import BaseTestCase

import pytest


@pytest.fixture
def module():
    return nikola.plugins.command.import_wordpress


@pytest.fixture
def import_command(module):
    command = module.CommandImportWordpress()
    command.onefile = False
    return command


@pytest.fixture
def import_filename():
    return os.path.abspath(os.path.join(os.path.dirname(__file__),
                           'wordpress_export_example.xml'))


def legacy_qtranslate_separate(text):
    """This method helps keeping the legacy tests covering various
    corner cases, but plugged on the newer methods."""
    text_bytes = text.encode("utf-8")
    modern_bytes = modernize_qtranslate_tags(text_bytes)
    modern_text = modern_bytes.decode("utf-8")
    return separate_qtranslate_tagged_langs(modern_text)


@pytest.mark.parametrize("content, french_translation, english_translation", [
    ("[:fr]Voila voila[:en]BLA[:]", "Voila voila", "BLA"),
    ("[:fr]Voila voila[:]COMMON[:en]BLA[:]", "Voila voila COMMON", "COMMON BLA"),
    ("<!--:fr-->Voila voila<!--:-->COMMON<!--:en-->BLA<!--:-->", "Voila voila COMMON", "COMMON BLA"),
    ("<!--:fr-->Voila voila<!--:-->COMMON<!--:fr-->MOUF<!--:--><!--:en-->BLA<!--:-->", "Voila voila COMMON MOUF", "COMMON BLA"),
    ("<!--:fr-->Voila voila<!--:--><!--:en-->BLA<!--:-->COMMON<!--:fr-->MOUF<!--:-->", "Voila voila COMMON MOUF", "BLA COMMON"),
], ids=["simple", "pre modern with intermission", "withintermission", "with uneven repartition", "with uneven repartition bis"])
def test_legacy_split_a_two_language_post(content, french_translation, english_translation):
    content_translations = legacy_qtranslate_separate(content)
    assert french_translation == content_translations["fr"]
    assert english_translation == content_translations["en"]


def test_conserves_qtranslate_less_post():
    content = """Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !"""
    content_translations = legacy_qtranslate_separate(content)
    assert 1 == len(content_translations)
    assert content == content_translations[""]


def test_modernize_a_wordpress_export_xml_chunk():
    test_dir = os.path.abspath(os.path.dirname(__file__))

    raw_export_path = os.path.join(test_dir,
                                   'wordpress_qtranslate_item_raw_export.xml')
    with open(raw_export_path, 'rb') as raw_xml_chunk_file:
        content = raw_xml_chunk_file.read()

    output = modernize_qtranslate_tags(content)

    modernized_xml_path = os.path.join(test_dir,
                                       'wordpress_qtranslate_item_modernized.xml')
    with open(modernized_xml_path, 'rb') as modernized_chunk_file:
        expected = modernized_chunk_file.read()

    assert expected == output


def test_modernize_qtranslate_tags():
        content = b"<!--:fr-->Voila voila<!--:-->COMMON<!--:fr-->MOUF<!--:--><!--:en-->BLA<!--:-->"
        output = modernize_qtranslate_tags(content)
        assert b"[:fr]Voila voila[:]COMMON[:fr]MOUF[:][:en]BLA[:]" == output


def test_split_a_two_language_post():
    content = """<!--:fr-->Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
<!--:--><!--:en-->If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
<!--:-->"""
    content_translations = legacy_qtranslate_separate(content)

    assert content_translations["fr"] == """Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
"""

    assert content_translations["en"] == """If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
"""


def test_split_a_two_language_post_with_teaser():
    content = """<!--:fr-->Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
<!--:--><!--:en-->If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
<!--:--><!--more--><!--:fr-->
Plus de détails ici !
<!--:--><!--:en-->
More details here !
<!--:-->"""
    content_translations = legacy_qtranslate_separate(content)
    assert content_translations["fr"] == """Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
 <!--more--> \n\
Plus de détails ici !
"""
    assert content_translations["en"] == """If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
 <!--more--> \n\
More details here !
"""


class BasicCommandImportWordpress(BaseTestCase):
    def setUp(self):
        self.module = nikola.plugins.command.import_wordpress
        self.import_command = self.module.CommandImportWordpress()
        self.import_command.onefile = False
        self.import_filename = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'wordpress_export_example.xml'))

    def tearDown(self):
        del self.import_command
        del self.import_filename


class CommandImportWordpressRunTest(BasicCommandImportWordpress):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.data_import = mock.MagicMock()
        self.site_generation = mock.MagicMock()
        self.write_urlmap = mock.MagicMock()
        self.write_configuration = mock.MagicMock()

        site_generation_patch = mock.patch('os.system', self.site_generation)
        data_import_patch = mock.patch(
            'nikola.plugins.command.import_wordpress.CommandImportWordpress.import_posts',
            self.data_import)
        write_urlmap_patch = mock.patch(
            'nikola.plugins.command.import_wordpress.CommandImportWordpress.write_urlmap_csv',
            self.write_urlmap)
        write_configuration_patch = mock.patch(
            'nikola.plugins.command.import_wordpress.CommandImportWordpress.write_configuration',
            self.write_configuration)

        self.patches = [site_generation_patch, data_import_patch,
                        write_urlmap_patch, write_configuration_patch]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        del self.data_import
        del self.site_generation
        del self.write_urlmap
        del self.write_configuration

        for patch in self.patches:
            patch.stop()
        del self.patches

        super(self.__class__, self).tearDown()

    def test_create_import(self):
        valid_import_arguments = (
            dict(options={'output_folder': 'some_folder'},
                 args=[self.import_filename]),
            dict(args=[self.import_filename]),
            dict(args=[self.import_filename, 'folder_argument']),
        )

        for arguments in valid_import_arguments:
            self.import_command.execute(**arguments)

            self.assertTrue(self.site_generation.called)
            self.assertTrue(self.data_import.called)
            self.assertTrue(self.write_urlmap.called)
            self.assertTrue(self.write_configuration.called)
            self.assertFalse(self.import_command.exclude_drafts)

    def test_ignoring_drafts(self):
        valid_import_arguments = (
            dict(options={'exclude_drafts': True}, args=[
                 self.import_filename]),
            dict(
                options={'exclude_drafts': True,
                         'output_folder': 'some_folder'},
                args=[self.import_filename]),
        )

        for arguments in valid_import_arguments:
            self.import_command.execute(**arguments)
            self.assertTrue(self.import_command.exclude_drafts)


def test_create_import_work_without_argument(import_command):
    # Running this without an argument must not fail.
    # It should show the proper usage of the command.
    import_command.execute()


@pytest.mark.parametrize("key, expected_value", [
    ('DEFAULT_LANG', 'de'),
    ('BLOG_TITLE', 'Wordpress blog title'),
    ('BLOG_DESCRIPTION', 'Nikola test blog ;) - with moré Ümläüts'),
    ('SITE_URL', 'http://some.blog/'),
    ('BLOG_EMAIL', 'mail@some.blog'),
    ('BLOG_AUTHOR', 'Niko'),
])
def test_populate_context(import_command, import_filename, key, expected_value):
    channel = import_command.get_channel_from_file(import_filename)
    import_command.html2text = False
    import_command.transform_to_markdown = False
    import_command.transform_to_html = False
    import_command.use_wordpress_compiler = False
    import_command.translations_pattern = '{path}.{lang}.{ext}'
    context = import_command.populate_context(channel)

    for required_key in ('POSTS', 'PAGES', 'COMPILERS'):
        assert required_key in context

    assert expected_value == context[key]


def test_importing_posts_and_attachments(module, import_command, import_filename):
    channel = import_command.get_channel_from_file(import_filename)
    import_command.base_dir = ''
    import_command.output_folder = 'new_site'
    import_command.squash_newlines = True
    import_command.no_downloads = False
    import_command.export_categories_as_categories = False
    import_command.export_comments = False
    import_command.html2text = False
    import_command.transform_to_markdown = False
    import_command.transform_to_html = False
    import_command.use_wordpress_compiler = False
    import_command.tag_saniziting_strategy = 'first'
    import_command.separate_qtranslate_content = False
    import_command.translations_pattern = '{path}.{lang}.{ext}'

    import_command.context = import_command.populate_context(channel)

    # Ensuring clean results
    # assert not import_command.url_map
    assert not module.links
    import_command.url_map = {}

    write_metadata = mock.MagicMock()
    write_content = mock.MagicMock()
    write_attachments_info = mock.MagicMock()
    download_mock = mock.MagicMock()

    with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.write_content', write_content):
        with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.write_metadata', write_metadata):
            with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.download_url_content_to_file', download_mock):
                with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.write_attachments_info', write_attachments_info):
                    with mock.patch('nikola.plugins.command.import_wordpress.os.makedirs'):
                        import_command.import_posts(channel)

    assert download_mock.called
    qpath = 'new_site/files/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png'
    download_mock.assert_any_call(
        'http://some.blog/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png',
        qpath.replace('/', os.sep))

    assert write_metadata.called
    write_metadata.assert_any_call(
        'new_site/pages/kontakt.meta'.replace('/', os.sep),
        'Kontakt', 'kontakt', '2009-07-16 20:20:32', '', [],
        **{'wp-status': 'publish'})

    assert write_content.called
    write_content.assert_any_call(
        'new_site/posts/2007/04/hoert.md'.replace('/', os.sep),
        """An image.

<img class="size-full wp-image-16" title="caption test" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="caption test" width="739" height="517" />

Some source code.

```Python

import sys
print sys.version

```

The end.
""",
        True)

    assert write_attachments_info.called
    write_attachments_info.assert_any_call('new_site/posts/2008/07/arzt-und-pfusch-s-i-c-k.attachments.json'.replace('/', os.sep),
                                           {10: {'wordpress_user_name': 'Niko',
                                                 'files_meta': [{'width': 300, 'height': 299},
                                                                {'width': 150, 'size': 'thumbnail', 'height': 150}],
                                                 'excerpt': 'Arzt+Pfusch - S.I.C.K.',
                                                 'date_utc': '2009-07-16 19:40:37',
                                                 'content': 'Das Cover von Arzt+Pfusch - S.I.C.K.',
                                                 'files': ['/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png',
                                                           '/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover-150x150.png'],
                                                 'title': 'Arzt+Pfusch - S.I.C.K.'}})

    write_content.assert_any_call(
        'new_site/posts/2008/07/arzt-und-pfusch-s-i-c-k.md'.replace('/', os.sep),
        '''<img class="size-full wp-image-10 alignright" title="Arzt+Pfusch - S.I.C.K." src="http://some.blog/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png" alt="Arzt+Pfusch - S.I.C.K." width="210" height="209" />Arzt+Pfusch - S.I.C.K.Gerade bin ich \xfcber das Album <em>S.I.C.K</em> von <a title="Arzt+Pfusch" href="http://www.arztpfusch.com/" target="_blank">Arzt+Pfusch</a> gestolpert, welches Arzt+Pfusch zum Download f\xfcr lau anbieten. Das Album steht unter einer Creative Commons <a href="http://creativecommons.org/licenses/by-nc-nd/3.0/de/">BY-NC-ND</a>-Lizenz.
Die Ladung <em>noisebmstupidevildustrial</em> gibts als MP3s mit <a href="http://www.archive.org/download/dmp005/dmp005_64kb_mp3.zip">64kbps</a> und <a href="http://www.archive.org/download/dmp005/dmp005_vbr_mp3.zip">VBR</a>, als Ogg Vorbis und als FLAC (letztere <a href="http://www.archive.org/details/dmp005">hier</a>). <a href="http://www.archive.org/download/dmp005/dmp005-artwork.zip">Artwork</a> und <a href="http://www.archive.org/download/dmp005/dmp005-lyrics.txt">Lyrics</a> gibts nochmal einzeln zum Download.''', True)
    write_content.assert_any_call(
        'new_site/pages/kontakt.md'.replace('/', os.sep), """<h1>Datenschutz</h1>
Ich erhebe und speichere automatisch in meine Server Log Files Informationen, die dein Browser an mich \xfcbermittelt. Dies sind:
<ul>
    <li>Browsertyp und -version</li>
    <li>verwendetes Betriebssystem</li>
    <li>Referrer URL (die zuvor besuchte Seite)</li>
    <li>IP Adresse des zugreifenden Rechners</li>
    <li>Uhrzeit der Serveranfrage.</li>
</ul>
Diese Daten sind f\xfcr mich nicht bestimmten Personen zuordenbar. Eine Zusammenf\xfchrung dieser Daten mit anderen Datenquellen wird nicht vorgenommen, die Daten werden einzig zu statistischen Zwecken erhoben.""", True)

    assert len(import_command.url_map) > 0

    assert 'http://some.blog/posts/2007/04/hoert.html' == import_command.url_map['http://some.blog/2007/04/hoert/']
    assert 'http://some.blog/posts/2008/07/arzt-und-pfusch-s-i-c-k.html' == import_command.url_map['http://some.blog/2008/07/arzt-und-pfusch-s-i-c-k/']
    assert 'http://some.blog/pages/kontakt.html' == import_command.url_map['http://some.blog/kontakt/']

    image_thumbnails = [
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-64x64.png',
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-300x175.png',
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-36x36.png',
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-24x24.png',
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png',
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png',
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-48x48.png',
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png',
        'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-150x150.png']

    for link in image_thumbnails:
        assert link in module.links


def test_transforming_content(import_command):
    """Applying markup conversions to content."""

    import_command.html2text = False
    import_command.transform_to_markdown = False
    import_command.transform_to_html = False
    import_command.use_wordpress_compiler = False
    import_command.translations_pattern = '{path}.{lang}.{ext}'

    transform_code = mock.MagicMock()
    transform_caption = mock.MagicMock()
    transform_newlines = mock.MagicMock()

    with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_code', transform_code):
        with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_caption', transform_caption):
            with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_multiple_newlines', transform_newlines):
                import_command.transform_content("random content", "wp", None)

    assert transform_code.called
    assert transform_caption.called
    assert transform_newlines.called


def test_transforming_source_code(import_command):
    """
    Tests the handling of sourcecode tags.
    """
    content = """Hello World.
[sourcecode language="Python"]
import sys
print sys.version
[/sourcecode]"""

    content = import_command.transform_code(content)

    assert '[/sourcecode]' not in content
    assert '[sourcecode language=' not in content

    replaced_content = """Hello World.
```Python

import sys
print sys.version

```"""
    assert content == replaced_content


def test_transform_caption(import_command):
    caption = '[caption id="attachment_16" align="alignnone" width="739" caption="beautiful picture"]<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />[/caption]'
    transformed_content = import_command.transform_caption(caption)

    expected_content = '<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />'

    assert transformed_content == expected_content


def test_transform_multiple_captions_in_a_post(import_command):
    content = """asdasdas
[caption id="attachment_16" align="alignnone" width="739" caption="beautiful picture"]<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />[/caption]
asdasdas
asdasdas
[caption id="attachment_16" align="alignnone" width="739" caption="beautiful picture"]<img class="size-full wp-image-16" title="pretty" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />[/caption]
asdasdas"""

    expected_content = """asdasdas
<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />
asdasdas
asdasdas
<img class="size-full wp-image-16" title="pretty" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />
asdasdas"""

    assert expected_content == import_command.transform_caption(content)


def test_transform_multiple_newlines(import_command):
    content = """This


has



way to many

newlines.


"""
    expected_content = """This

has

way to many

newlines.

"""
    import_command.squash_newlines = False
    assert content == import_command.transform_multiple_newlines(content)

    import_command.squash_newlines = True
    assert expected_content == import_command.transform_multiple_newlines(content)


def test_transform_caption_with_link_inside(import_command):
    content = """[caption caption="Fehlermeldung"]<a href="http://some.blog/openttd-missing_sound.png"><img class="size-thumbnail wp-image-551" title="openttd-missing_sound" src="http://some.blog/openttd-missing_sound-150x150.png" alt="Fehlermeldung" /></a>[/caption]"""
    transformed_content = import_command.transform_caption(content)

    expected_content = """<a href="http://some.blog/openttd-missing_sound.png"><img class="size-thumbnail wp-image-551" title="openttd-missing_sound" src="http://some.blog/openttd-missing_sound-150x150.png" alt="Fehlermeldung" /></a>"""
    assert expected_content == transformed_content


def test_get_configuration_output_path(import_command):
    import_command.output_folder = 'new_site'
    default_config_path = os.path.join('new_site', 'conf.py')

    import_command.import_into_existing_site = False
    assert default_config_path == import_command.get_configuration_output_path()

    import_command.import_into_existing_site = True
    config_path_with_timestamp = import_command.get_configuration_output_path()

    assert default_config_path != config_path_with_timestamp
    assert import_command.name in config_path_with_timestamp


def test_write_content_does_not_detroy_text(import_command):
    content = b"""FOO"""
    open_mock = mock.mock_open()
    with mock.patch('nikola.plugins.basic_import.open', open_mock, create=True):
        import_command.write_content('some_file', content)

    open_mock.assert_has_calls([
        mock.call(u'some_file', u'wb+'),
        mock.call().__enter__(),
        mock.call().write(b'<html><body><p>FOO</p></body></html>'),
        mock.call().__exit__(None, None, None)]
    )


def test_configure_redirections(import_command):
    """
    Testing the configuration of the redirections.

    We need to make sure that we have valid sources and target links.
    """
    url_map = {
        '/somewhere/else': 'http://foo.bar/posts/somewhereelse.html'
    }

    redirections = import_command.configure_redirections(url_map)

    assert 1 == len(redirections)
    assert ('somewhere/else/index.html', '/posts/somewhereelse.html') in redirections

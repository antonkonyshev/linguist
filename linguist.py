# -*- coding: utf-8 -*-
"""
.. module:: linguist
   :platform: Unix, Windows
   :synopsis: Zim plugin for linguistic assistance

.. moduleauthor:: Anton Konyshev <anton.konyshev@gmail.com>

"""
# Copyright (c) 2014, Anton Konyshev

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import gtk

import google_translate_api as gtapi

from zim.plugins import PluginClass, WindowExtension
from zim.plugins import extends
from zim.gui.widgets import RIGHT_PANE, PANE_POSITIONS
from zim.actions import action


__version__ = u'0.1a1'


class LinguistPlugin(PluginClass):
    """Linguist plugin configuration, default values, and constants."""

    plugin_info = {
        u'name': _(u'Linguist'),
        u'description': u'\n\n'.join([
            _(u"This plugin adds an extra widget providing a linguistic "
              u"assistance."),
            u'{0}: {1}.'.format(
                _(u'Version'), globals().get(u'__version__', _(u'Unknown')))]),
        u'author': u'Anton Konyshev',
        u'help': u'Plugins:Linguist',
    }

    DEFAULT_NATIVE_LANG = u'en'
    DEFAULT_FOREIGN_LANG = u'ru'
    AVAILABLE_LANGUAGES = (
        (u'af', _(u'Afrikaans')), (u'sq', _(u'Albanian')),
        (u'ar', _(u'Arabic')), (u'az', _(u'Azerbaijani')),
        (u'bg', _(u'Bulgarian')), (u'ca', _(u'Catalan')),
        (u'zh-CN', _(u'Chinese Simplified')),
        (u'zh-TW', _(u'Chinese Traditional')),
        (u'hr', _(u'Croatian')), (u'cs', _(u'Czech')), (u'da', _(u'Danish')),
        (u'nl', _(u'Dutch')), (u'en', _(u'English')), (u'eo', _(u'Esperanto')),
        (u'et', _(u'Estonian')), (u'tl', _(u'Filipino')),
        (u'fi', _(u'Finnish')), (u'fr', _(u'French')), (u'gl', _(u'Galician')),
        (u'ka', _(u'Georgian')), (u'de', _(u'German')), (u'el', _(u'Greek')),
        (u'gu', _(u'Gujarati')), (u'ht', _(u'Haitian Creole')),
        (u'iw', _(u'Hebrew')), (u'hi', _(u'Hindi')), (u'hu', _(u'Hungarian')),
        (u'is', _(u'Icelandic')), (u'id', _(u'Indonesian')),
        (u'ga', _(u'Irish')), (u'it', _(u'Italian')), (u'ja', _(u'Japanese')),
        (u'kn', _(u'Kannada')), (u'ko', _(u'Korean')), (u'la', _(u'Latin')),
        (u'lv', _(u'Latvian')), (u'lt', _(u'Lithuanian')),
        (u'mk', _(u'Macedonian')), (u'ms', _(u'Malay')),
        (u'mt', _(u'Maltese')), (u'no', _(u'Norwegian')),
        (u'fa', _(u'Persian')), (u'pl', _(u'Polish')),
        (u'pt', _(u'Portuguese')), (u'ro', _(u'Romanian')),
        (u'ru', _(u'Russian')), (u'sr', _(u'Serbian')), (u'sk', _(u'Slovak')),
        (u'sl', _(u'Slovenian')), (u'es', _(u'Spanish')),
        (u'sw', _(u'Swahili')), (u'sv', _(u'Swedish')), (u'ta', _(u'Tamil')),
        (u'te', _(u'Telugu')), (u'th', _(u'Thai')), (u'tr', _(u'Turkish')),
        (u'uk', _(u'Ukrainian')), (u'ur', _(u'Urdu')),
        (u'vi', _(u'Vietnamese')), (u'cy', _(u'Welsh')), (u'yi', _(u'Yiddish'))
    )

    plugin_preferences = (
        (u'pane', u'choice', _(u'Position in the window'), RIGHT_PANE,
            PANE_POSITIONS),
        (u'nativelang', u'choice', _(u'Your native language'),
            DEFAULT_NATIVE_LANG, AVAILABLE_LANGUAGES),
        (u'foreignlang', u'choice', _(u'Foreign language'),
            DEFAULT_FOREIGN_LANG, AVAILABLE_LANGUAGES),
    )


@extends('MainWindow')
class MainWindowExtension(WindowExtension):
    """Extension for the Zim main window."""

    uimanager_xml = u"""
    <ui>
    <menubar name='menubar'>
        <menu action='tools_menu'>
            <placeholder name='plugin_items'>
                <menuitem action='translate_from' />
                <menuitem action='translate_into' />
            </placeholder>
        </menu>
    </menubar>
    </ui>
    """

    TABNAME = _(u'Linguist')

    def __init__(self, plugin, window):
        """Zim window extension for Linguist plugin.

        :param plugin: Linguist plugin instance
        :param window: Zim window instance

        """
        super(MainWindowExtension, self).__init__(plugin, window)

        self.translator = Translator()
        self.widget = LinguistWidget()
        self.on_preferences_changed(plugin.preferences)
        self.connectto(plugin.preferences, 'changed',
                       self.on_preferences_changed)

    def on_preferences_changed(self, preferences):
        """Handles changes of plugin's settings."""
        if getattr(self, u'widget', None) is not None:
            try:
                self.window.remove(self.widget)
            except ValueError:
                pass
            self._nativelang = preferences['nativelang']
            self._foreignlang = preferences['foreignlang']
            self.window.add_tab(self.TABNAME, self.widget, preferences['pane'])
            self.widget.show_all()

    def teardown(self):
        """Destroys the widget."""
        self.window.remove(self.widget)
        self.widget.destroy()
        del self.widget

    def _get_native_lang(self):
        """Returns "native language" parameter.

        :returns: Native language code
        :rtype: unicode

        """
        return getattr(self, u'_nativelang',
                       LinguistPlugin.DEFAULT_NATIVE_LANG)

    def _get_foreign_lang(self):
        """Returns "foreign language" parameter.

        :returns: Foreign language code
        :rtype: unicode

        """
        return getattr(self, u'_foreignlang',
                       LinguistPlugin.DEFAULT_FOREIGN_LANG)

    def _get_word_bounds(self):
        """Returns signs of word bounds.

        :returns: Collection of boundary signs
        :rtype: tuple of unicodes

        """
        return (u' ', u'\n', u'\t')

    def _get_sentence_bounds(self):
        """Returns signs of sentence bounds.

        :returns: Collection of boundary signs
        :rtype: tuple of unicodes

        """
        return (u'.', u'!', u'?', u'\n\n')

    def _get_text_segment(self, buf, bounds, include_end_bound=False):
        """Extracts a segment of text under the cursor.

        :param buf: Text buffer with the text
        :type buf: :class:`gtk.TextBuffer`
        :param bounds: Collection of boundary signs
        :type bounds: tuple of unicodes
        :param bool include_end_bound: Include right boundary character or not
        :returns: The desired text segment
        :rtype: unicode

        """
        it = buf.get_iter_at_mark(buf.get_insert())
        starts = [buf.get_start_iter()]
        ends = [buf.get_end_iter()]
        for bound in bounds:
            try:
                start = it.backward_search(bound, gtk.TEXT_SEARCH_TEXT_ONLY)[
                    int(not len(bound) > 1)]
            except TypeError:
                pass
            else:
                if start:
                    starts.append(start)
            try:
                end = it.forward_search(bound, gtk.TEXT_SEARCH_TEXT_ONLY)[
                    1 if include_end_bound else 0]
            except TypeError:
                pass
            else:
                if end:
                    ends.append(end)
        starts.sort(key=lambda x: x.get_offset(), reverse=True)
        ends.sort(key=lambda x: x.get_offset())
        return buf.get_text(starts[0], ends[0])

    def _translate(self, source_lang, target_lang):
        """Performs translations.

        :param source_lang: Language of the source text
        :type source_lang: unicode or str
        :param target_lang: Target language for the translation
        :type target_lang: unicode or str

        """
        self.widget.clear()

        buf = self.window.pageview.view.get_buffer()
        word = self._get_text_segment(buf, self._get_word_bounds())
        sentence = self._get_text_segment(buf, self._get_sentence_bounds(),
                                          include_end_bound=True)

        sentence_translation = self.translator.trans_sentence(
            source_lang, target_lang, sentence)
        if sentence_translation:
            self.widget.show_sentence_translation(
                sentence_translation.get_result(bold=True))
            reverse_translation = self.translator.trans_sentence(
                target_lang, source_lang,
                sentence_translation.get_translation())
            if reverse_translation:
                self.widget.show_sentence_translation(
                    reverse_translation.get_result(), reverse=True)

        word_translation = self.translator.trans_details(source_lang,
                                                         target_lang, word)
        if word_translation:
            self.widget.show_word_translation(word_translation.get_result())
            self.widget.show_word_forms(word_translation)

    @action(_('_Translate from'), accelerator='F4')
    def translate_from(self):
        """Requests translation from the foreign language to the native
        language.

        """
        self._translate(self._get_foreign_lang(), self._get_native_lang())

    @action(_('_Translate into'), accelerator='F5')
    def translate_into(self):
        """Requests translation from the native language to the foreign
        language.

        """
        self._translate(self._get_native_lang(), self._get_foreign_lang())


class LinguistWidget(gtk.VBox):
    """Plugin's widget."""

    def __init__(self):
        """Pane that provides the displaying of translations."""
        super(LinguistWidget, self).__init__()
        tmp = gtk.Label(u'<u>{0}</u>'.format(_(u'Sentence translation')))
        tmp.set_use_markup(True)
        self.pack_start(tmp, False, True, 3)
        self.fore_sentence = gtk.Label()
        self.fore_sentence.set_alignment(0, 0.5)
        self.fore_sentence.set_use_markup(True)
        self.pack_start(self.fore_sentence, False, False, 3)
        tmp = gtk.Label(u'<u>{0}</u>'.format(_(u'Reverse translation')))
        tmp.set_use_markup(True)
        self.pack_start(tmp, False, True, 3)
        self.back_sentence = gtk.Label()
        self.back_sentence.set_use_markup(True)
        self.back_sentence.set_alignment(0, 0.5)
        self.pack_start(self.back_sentence, False, False, 3)
        tmp = gtk.Label(u'<u>{0}</u>'.format(_(u'Word')))
        tmp.set_use_markup(True)
        self.pack_start(tmp, False, True, 3)
        self.word = gtk.Label()
        self.word.set_use_markup(True)
        self.word.set_alignment(0, 0.5)
        self.pack_start(self.word, False, False, 3)
        self.forms = []

    def show_sentence_translation(self, text, reverse=False):
        """Shows a translation of a sentence.

        :param text: Translation result
        :type text: unicode or str
        :param bool reverse: Is it reverse translation or not

        """
        if reverse:
            self.back_sentence.set_markup(text)
        else:
            self.fore_sentence.set_markup(text)

    def show_word_translation(self, text):
        """Shows a translation of a word.

        :param text: Translation result
        :type text: unicode or str

        """
        self.word.set_markup(text)

    def show_word_forms(self, translation_result):
        """Shows a list of synomyms with their translations.

        :param translation_result: Result of a translation
        :type translation_result: :class:`TranslationResult`

        """
        for base, pos, entries in translation_result.get_forms():
            label = gtk.Label(u'\n<i>{0} | <u>{1}</u></i>'.format(base, pos))
            label.set_alignment(0, 0.5)
            label.set_use_markup(True)
            self.pack_start(label, False, False, 0)
            self.forms.append(label)
            for word, reverses, score in entries:
                label = gtk.Label(u'<b>{0}</b> [{1}]: {2}'.format(
                    word, unicode(score), u', '.join([
                        reverse for reverse in reverses])))
                label.set_alignment(0, 0.5)
                label.set_use_markup(True)
                self.pack_start(label, False, False, 0)
                self.forms.append(label)
        self.show_all()

    def clear(self):
        """Removes results of last translation from pane."""
        map(lambda x: x.destroy(), self.forms)
        self.word.set_text(u'')
        self.back_sentence.set_text(u'')
        self.fore_sentence.set_text(u'')


class Translator(gtapi.TranslateService):
    """Google Translate API client"""

    def trans_details(self, source_lang, target_lang, text):
        """Translates a text or word and returns detailed result.

        :param source_lang: Language of the source text
        :type source_lang: unicode or str
        :param target_lang: Target language for the translation
        :type target_lang: unicode or str
        :returns: Translation result or None, if response hasn't been received
        :rtype: :class:`TranslationResult` or None

        """
        response = super(Translator, self).trans_details(source_lang,
                                                         target_lang, text)
        if response:
            try:
                sentence = response.get(u'sentences', [])[0]
            except IndexError:
                sentence = {}
            return TranslationResult(
                source_lang=source_lang, target_lang=target_lang,
                origin=sentence.get(u'orig', u''),
                translation=sentence.get(u'trans', u''),
                translit=sentence.get(u'translit', u''),
                forms=[(form.get(u'base_form', u''), form.get(u'pos', u''),
                        [(entry.get(u'word', u''),
                          entry.get(u'reverse_translation', []),
                          int(entry.get(u'score', 0.0) * 10000))
                         for entry in form.get(u'entry', [])])
                       for form in response.get(u'dict', [])])
        return None

    def trans_sentence(self, source_lang, target_lang, text):
        """Translates a text or word and returns brief result.

        :param source_lang: Language of the source text
        :type source_lang: unicode or str
        :param target_lang: Target language for the translation
        :type target_lang: unicode or str
        :returns: Translation result or None, if response hasn't been received
        :rtype: :class:`TranslationResult` or None

        """
        response = super(Translator, self).trans_sentence(source_lang,
                                                          target_lang, text)
        if response:
            return TranslationResult(
                translation=response, source_lang=source_lang,
                target_lang=target_lang)
        return None


class TranslationResult(object):
    """Contains the translation data."""

    def __init__(self, source_lang=None, target_lang=None, origin=None,
                 translation=None, translit=None, forms=[]):
        """Data model that contains the translation parameters and results.

        :param source_lang: Language of the source text
        :type source_lang: unicode or str
        :param target_lang: Target language for the translation
        :type target_lang: unicode or str
        :param unicode origin: The source text
        :param unicode translation: Result of the translation
        :param unicode translit: Transliteration of the source text
        :param list forms: Word forms and synonyms

        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.origin = origin
        self.translation = translation
        self.translit = translit
        self.forms = forms

    def is_detailed(self):
        """Indicates is the translation result detailed or not.

        :returns: Detail level of the translation result
        :rtype: bool

        """
        return bool(len(getattr(self, u'forms', [])))

    def get_translation(self):
        """Returns the translation result.

        :returns: Translation result
        :rtype: unicode

        """
        return getattr(self, u'translation', u'')

    def get_result(self, bold=False):
        """Returns the translation result with markup.

        :param bool bold: Emphasize the translation or not
        :returns: Translation result with markup (html-tags)
        :rtype: unicode

        """
        if getattr(self, u'translation', None) is None:
            return u''
        result = self.translation
        if bold:
            result = u''.join([u'<b>', result, u'</b>'])
        if getattr(self, u'origin', None):
            result = u' | '.join([u'<b>{0}</b>'.format(result), self.origin])
        return result

    def get_forms(self):
        """Returns the list of synonyms and their translations.

        :returns: List of word forms and synonyms
        :rtype: list

        """
        return getattr(self, u'forms', [])

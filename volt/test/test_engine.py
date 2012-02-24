#!/usr/bin/env python
# -*- coding: utf8 -*-

# tests for volt.engine

import glob
import os
import re
import unittest
from datetime import datetime

from volt import ConfigError, ContentError, ParseError
from volt.config import Session
from volt.engine.base import BaseEngine, BaseUnit, MARKUP
from volt.engine.blog import BlogEngine, BlogUnit


class TestBaseEngine(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.content_dir = os.path.join(self.test_dir, 'fixtures', 'project', \
                'content', 'blog', '01')

    def test_init(self):
        # test if BaseUnit subclass is used to initialize engine
        self.assertRaises(TypeError, BaseEngine.__init__, ) 
    
    def test_globdir(self):
        # test if whole directory globbing for files work
        self.engine = BaseEngine(BaseUnit)
        dir_content = ['01_pass.md', 'mockdir']
        dir_content = [os.path.join(self.content_dir, x) for x in dir_content].sort()
        self.assertEqual(self.engine.globdir(self.content_dir).sort(), dir_content)
      

class TestBaseUnit(unittest.TestCase):

    def setUp(self):
        header = {'title': 'Logos',
                  'tags' : 'ripley, ash, kane    ',
                  'cats' : 'wickus;christopher;koobus;',
                 }
        self.unit = BaseUnit()
        self.unit.content = 'Content'
        for field in header:
            setattr(self.unit, field, header[field])
        self.unit.id = '01.md'

    def test_check_required(self):
        # test required fields check
        req = ('title', 'surprise', )
        self.assertRaises(ContentError, self.unit.check_required, req)

    def test_process_into_list(self):
        # test if specified fields are processed into lists
        tags = ['ripley', 'ash', 'kane']
        self.unit.process_into_list(['tags'], ', ')
        self.assertEqual(self.unit.tags, tags)
        cats = ['wickus', 'christopher', 'koobus']
        self.unit.process_into_list(['cats'], ';')
        self.assertEqual(self.unit.cats, cats)

    def test_set_markup(self):
        # test if markup is set correctly
        self.unit.set_markup(MARKUP)
        self.assertEqual(self.unit.markup, 'markdown')
        # test if exception is raised for unlisted markup
        setattr(self.unit, 'markup', 'xml')
        self.assertRaises(ContentError, self.unit.set_markup, MARKUP)

    def test_slugify(self):
        slugify = self.unit.slugify
        self.assertEqual(slugify('Move along people, this is just a test'),
                'move-along-people-this-is-just-test')
        self.assertEqual(slugify('What does it mean to say !&^#*&@$))*((&?'),
                 'what-does-it-mean-to-say')
        self.assertEqual(slugify('What about the A* search algorithm?'),
                 'what-about-the-a-search-algorithm')
        self.assertEqual(slugify('--This- is a bad -- -*&( ---___- title---'),
                 'this-is-bad-title')
        self.assertEqual(slugify("Hors d'oeuvre, a fully-loaded MP5, and an astronaut from Ann Arbor."),
                 'hors-doeuvre-fully-loaded-mp5-and-astronaut-from-ann-arbor')
        self.assertEqual(slugify('Kings of Convenience - Know How (feat. Feist)'),
                 'kings-of-convenience-know-how-feat-feist')
        self.assertEqual(slugify('A Journey Through the Himalayan Mountains. Part 1: An Unusual Guest'),
                 'journey-through-the-himalayan-mountains-part-1-unusual-guest')
        self.assertRaises(AssertionError, slugify, 'Röyksopp - Eple')
        self.assertRaises(AssertionError, slugify, '宇多田ヒカル')
        self.assertRaises(ContentError, slugify, '&**%&^%&$-')

    def test_set_permalink(self):
        self.unit.slug = self.unit.slugify('Yo Dawg!')
        self.unit.time = datetime(2009, 1, 28, 16, 47)
        self.unit.set_permalink('{time:%Y/%m/%d}/{slug}', '/base')
        self.assertEqual(self.unit.permalink, '/base/2009/01/28/yo-dawg')
        self.unit.set_permalink('{time:%Y}/mustard/{time:%m}/{slug}')
        self.assertEqual(self.unit.permalink, '2009/mustard/01/yo-dawg')
        self.assertRaises(ContentError, self.unit.set_permalink, 'bali/{beach}/party')

class TestBlogEngine(unittest.TestCase):

    def setUp(self):
        from volt.config import Session
        # set up dirs and Session
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.join(self.test_dir, 'fixtures', 'project')
        self.content_dir = os.path.join(self.project_dir, 'content', 'blog')
        default_conf = 'volt.test.fixtures.config.default'
        self.conf = Session(default_conf, self.project_dir).BLOG
        self.engine = BlogEngine(BlogUnit)

    def tearDown(self):
        del self.engine


class TestBlogUnit(unittest.TestCase):

    def setUp(self):
        # set up dirs and Session
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.join(self.test_dir, 'fixtures', 'project')
        self.content_dir = os.path.join(self.project_dir, 'content', 'blog')
        default_conf = 'volt.test.fixtures.config.default'
        self.config = Session(default_conf, self.project_dir).BLOG
        self.delim = re.compile(r'^---$', re.MULTILINE)

    def test_init(self):
        # test if blog post is processed correctly
        fname = glob.glob(os.path.join(self.content_dir, 'pass', '*'))[0]
        unit_obj = BlogUnit(fname, self.delim, self.config)
        self.assertEqual(unit_obj.id, fname)
        self.assertEqual(unit_obj.time, datetime(2004, 3, 13, 22, 10))
        self.assertEqual(unit_obj.title, 'Jabberwock')
        self.assertEqual(unit_obj.extra, 'ice cream please')
        self.assertIsNone(unit_obj.empty)
        content = u'Should be parsed correctly.\n\nHey look, unicode: \u042d\u0439, \u0441\u043c\u043e\u0442\u0440\u0438, \u042e\u043d\u0438\u043a\u043e\u0434'
        self.assertEqual(unit_obj.content, content)
        self.assertEqual(unit_obj.slug, 'jabberwock')

    def test_init_header_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'fail', '02*'))[0]
        self.assertRaises(ParseError, BlogUnit, fname, self.delim, self.config)

    def test_init_header_typo(self):
        from yaml import scanner
        fname = glob.glob(os.path.join(self.content_dir, 'fail', '03*'))[0]
        self.assertRaises(scanner.ScannerError, BlogUnit, fname, self.delim, self.config)

    def test_init_markup_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'fail', '04*'))[0]
        self.assertEqual(BlogUnit(fname, self.delim, self.config).markup, 'html')


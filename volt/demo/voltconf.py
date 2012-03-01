# Volt configurations file

import os

from volt.config.base import Config


# Volt configurations
VOLT = Config(

    # Flag for colored terminal output
    COLORED_TEXT = True,
)

# General project configurations
SITE = Config(

    # Your site name
    TITLE = 'Volt Demo Site',

    # Your site URL
    URL = '',

    # Your site description
    DESC = 'because static sites have potential',

    # Engines used in generating the site
    # Available engines are 'page', 'blog', and 'collection'
    # To disable an engine, just remove its name from this list
    ENGINES = ('blog', 'plain', ),

    # Plugins used in site generation
    # These are run according to the order they are listed here
    PLUGINS = (
        ('syntax', ['blog']),
        ('markdown', ['blog', 'plain']),
    ),
)

# Blog engine configurations
BLOG = Config(
  
    # URL for all blog content relative to root URL
    URL = 'blog',

    # Blog posts permalink, relative to blog URL
    PERMALINK = '{time:%Y/%m/%d}/{slug}',

    # Global values to be set to all blog posts
    GLOBAL_FIELDS = {'author': 'Ellen Ripley', },

    # The number of displayed posts per pagination page
    POSTS_PER_PAGE = 2, 
)

# Page engine configurations
PLAIN = Config(

    # URL for all page content relative to root URL
    URL = '/',

    # Page permalink, relative to page URL
    PERMALINK = '{slug}',
)

# Plugin configurations
PLUGINS = Config(

    SYNTAX_CSS_FILE = os.path.join(os.getcwd(), 'site', 'css', 'syntax_highlight.css'),
)

.. _format:

Format and Themes
=================

Overview
--------

How the report looks is defined in YAML, in the same way as the plan. The title, the logo in the banner, \
and the colours, fonts and chart colours of every theme are all settings that can be changed. Nothing \
needs to be changed in the tool.

There are two input types, found in the input directory like any other:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Type
     - Defines
   * - ``format_definitions``
     - The title and other text, the logo, which theme the report opens on, extra CSS, and the default unit of \
       task effort (``task_unit``)
   * - ``themes_definitions``
     - Themes: the colours and fonts of the page and charts. They are listed in the *Theme* chooser at the \
       top right of every page

Both are optional. With neither the report looks as it always has. The defaults are in the ``defaults`` \
directory of the package, ``format.yaml`` and ``themes.yaml``, and are a good starting point to copy from.

Two complete examples are provided, and are described at the end of this page.

.. image:: /images/format_eighties.png
   :align: center

Format
------

``data`` is a single mapping. Only the keys given are changed, so a format file can be as short as a title. \
If more than one format is found they are applied in file order, and later ones win.

.. code-block:: yaml

    type: "format_definitions"
    data:
      title: "Acme Project Management"
      kicker: "Planning"
      generated: "Report generated {stamp}"
      default_theme: "dark"
      logo:
        file: "acme.png"
        alt: "Acme"
        link: "https://acme.example.com"

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Field
     - Default
     - Description
   * - ``title``
     - ``Apheleia Project Management``
     - Title of the top level page, in the banner and the browser tab. The other pages are titled after what they show
   * - ``kicker``
     - ``Project Management``
     - Small heading above the title of the top level page
   * - ``generated``
     - ``Report generated {stamp}``
     - Line under the title of every page. ``{stamp}`` is replaced by the date and time the report was made
   * - ``theme_label``
     - ``Theme``
     - Label of the theme chooser. The chooser is left out if there is only one theme
   * - ``default_theme``
     - ``default``
     - Theme used until the viewer chooses another. The choice a viewer makes is remembered by their browser
   * - ``builtin_themes``
     - ``true``
     - Offer the themes that come with the tool: ``default``, ``monochrome`` and ``dark``. Set to ``false`` to offer \
       only the themes given in ``themes_definitions``
   * - ``logo``
     - the Apheleia logo
     - The image at the right of the banner, described below. ``null`` for no logo
   * - ``css``
     - none
     - Extra CSS added to every page, after the themes, for changes that are the same in every theme
   * - ``task_unit``
     - ``md``
     - Unit of task effort (``estimate``, ``spent`` and ``remaining``) given as a plain number, for every task in \
       the input: ``md``, ``mw``, ``mm`` or ``my``. Effort given with a unit is not affected. See :doc:`../inputs/tasks`

Logo
^^^^

The logo is embedded in each page, so the report does not need any other files. Giving a ``logo`` replaces \
the Apheleia logo completely, including its link. Give exactly one of ``file`` and ``svg``:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Description
   * - ``file``
     - Path to a ``png``, ``jpg``, ``gif``, ``webp`` or ``svg`` image. A relative path is relative to the YAML file
   * - ``svg``
     - SVG markup written in the YAML. Because it is part of the page it can use the theme's variables, for \
       example ``fill="var(--accent)"``, so the logo changes with the theme
   * - ``alt``
     - Text for screen readers. Default ``logo``
   * - ``link``
     - Address opened in a new tab when the logo is clicked. Default none, so the logo is not a link
   * - ``tooltip``
     - Text shown when hovering over the logo. Default none
   * - ``height``
     - Height in pixels from 8 to 300. Default 44

Themes
------

``data`` is a list of themes. A theme only has to give what is different, since anything it does not give \
is taken from the built-in ``default`` theme, or from the theme named in ``extends``. This is the built-in theme \
even if the input replaces ``default``, so that a replacement can itself give only what it changes.

.. code-block:: yaml

    type: "themes_definitions"
    data:
      - name: "sepia"
        label: "Sepia"
        variables:
          page: "#f4ecd8"
          card: "#fffaf0"
          accent: "#8a5a2b"
        chart:
          plot: "#f8f1e0"

A theme with the name of a built-in theme replaces it. Otherwise it is added after the built-in themes, in \
file order.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Description
   * - ``name``
     - Required. Letters, numbers, ``-`` and ``_``. Used to select the theme in ``default_theme`` and ``extends``
   * - ``label``
     - Name shown in the chooser. Default is the name
   * - ``extends``
     - Name of another theme to take the values that are not given from, instead of ``default``. Themes can \
       extend each other in any order but not in a loop
   * - ``dark``
     - ``true`` for a dark theme, so that the browser draws its own controls and scroll bars dark. Default \
       is that of the theme extended
   * - ``variables``
     - The colours and fonts of the page, below
   * - ``chart``
     - The colours of the charts, below
   * - ``bars``
     - How the bars of the charts are coloured, below
   * - ``css``
     - Extra CSS for this theme only, below

Variables
^^^^^^^^^

Each variable is a CSS custom property, so ``page`` is used as ``var(--page)``. A value is any CSS value for \
the property: a colour, a gradient, a font list, or a shadow. A value must not contain ``{``, ``}``, ``<`` or ``>``.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Used for
   * - ``band-dark``, ``band-mid``, ``band-light``
     - Dark bands: the toolbar, table headings and the main tiles. Headings and tiles are a gradient of mid to light
   * - ``on-dark``
     - Text on the bands, the banner and the table headings
   * - ``accent``, ``accent-dark``, ``accent-2``
     - Badges, the information badge, selected table pages and hover colours
   * - ``on-accent``, ``on-bad``
     - Text on the accent colour, and on the ``bad`` colour
   * - ``page``, ``card``
     - Background of the page, and of the cards that hold each chart and table
   * - ``ink``, ``muted``, ``title``, ``link``
     - Body text, secondary text, titles and links
   * - ``line``, ``shadow``
     - Borders and shadows
   * - ``zebra``, ``hover``, ``head-a``, ``head-b``, ``row-odd``, ``row-line``
     - Table rows, row under the pointer, the card headings, and the lines between rows
   * - ``filter-bg``, ``input-bg``, ``input-border``
     - Table filters and inputs
   * - ``tab-bar``, ``tab-hover``
     - Tabs
   * - ``current``, ``bad``, ``over``
     - The current milestone, overruns and missing estimates, and over estimate rows
   * - ``header-bg``, ``header-shadow``
     - Background of the banner, which can be a gradient or an image, and its shadow
   * - ``kicker-text``, ``meta-text``
     - The small heading and the line under the title in the banner
   * - ``toolbar-text``
     - Text in the toolbar
   * - ``logo-bg``, ``logo-filter``
     - Background behind the logo, and a CSS filter for it, for example ``grayscale(1)``
   * - ``tooltip-bg``, ``tooltip-text``
     - Hover tips
   * - ``font``, ``title-font``
     - Fonts of the text, and of the titles
   * - ``radius``
     - Corner radius of cards and tabs

Any other name is also written as a variable, so ``logo-ink: "#141414"`` can be used in a logo's SVG as \
``var(--logo-ink)`` or in the CSS of the format or theme.

Chart
^^^^^

The charts are drawn when the report is made, and recoloured in the browser when the theme changes. \
These are all optional:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Colour
     - Used for
   * - ``paper``, ``plot``
     - Background of the chart and of the area the bars are drawn in
   * - ``font``, ``font_family``
     - Colour and font of the text
   * - ``grid_x``, ``grid_y``
     - Grid lines
   * - ``line``
     - Axis lines
   * - ``legend_bg``, ``legend_border``
     - Key of the chart

Bars
^^^^

By default every name keeps the colour the chart gave it, so the same name has the same colour on every \
chart. A theme can instead give either:

.. code-block:: yaml

    # A list of colours, used in turn
    bars: ["#ff2d95", "#00e5ff", "#ffe600"]

    # Or a ramp of lightness, as the monochrome theme uses. Hue is 0 to 360, saturation and lightness 0 to 100
    bars:
      ramp:
        hue: 35
        saturation: 8
        lightness: [14, 62]

CSS
^^^

``css`` gives rules for this theme only, for things that cannot be done with a variable such as a glow or \
a border. Write ``@theme`` where the selector of the theme should go, so the rules only apply to it:

.. code-block:: yaml

    css: |
      @theme .page-title { text-shadow: 0 0 12px #ff2d95; }
      @theme .card { border-color: #ff2d95; }

becomes ``html[data-theme="neon"] .page-title { ... }``.

Errors
------

The format is checked before the report is written, and the script stops in the same way as for the plan. \
The cases caught are:

- a field that is not expected, in the format, a theme, the logo, or the chart colours of a theme
- a ``default_theme`` or ``extends`` that is not a theme, and themes that extend each other in a loop
- a theme defined twice, or a theme name that is not letters, numbers, ``-`` and ``_``
- a logo with both or neither of ``file`` and ``svg``, a file that is missing or not an image, and a ``height`` out of range
- a value containing ``{``, ``}``, ``<`` or ``>``
- ``bars`` that is not ``original``, a list of colours or a ramp
- no themes to offer, because ``builtin_themes`` is ``false`` and none are given

Examples
--------

``examples/format`` has two reports of the same plan with their own format.

``eighties`` is bright, neon and geometric, in the style of an eighties teen sitcom. It changes the title and text, \
embeds ``logo.svg`` as the logo, and **adds** two themes to the built-in ones: ``Neon Night``, which the report opens on, \
and ``Bayside Pastel``. Their banners are a gradient with a pattern of shapes drawn over it, and ``Neon Night`` \
uses ``css`` for the glow.

.. literalinclude:: ../../../examples/format/eighties/format.yaml
    :language: yaml

``noir`` is black and white, in the style of a classic film noir. It turns the built-in themes off and **replaces** them \
with just two, ``Noir Light`` and ``Noir Dark``. The logo is a silhouette of a man in a hat with a cigarette, written \
as SVG in the format. It uses ``--logo-ink`` and ``--logo-bg`` from the theme, so the silhouette inverts with it. ``Noir Dark`` \
uses ``extends`` to take the fonts and chart font of ``Noir Light`` and gives only the colours that change.

.. image:: /images/format_noir.png
   :align: center

.. literalinclude:: ../../../examples/format/noir/format.yaml
    :language: yaml

"""
The format of the report: its text, logo and themes.

All of it is defined in YAML. The defaults are in the ``defaults`` directory of the package and a user
changes them with ``format_definitions`` and ``themes_definitions`` files in the input directory.
"""

import base64
import html as _html
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ._utils import EFFORT_UNITS, UNIT_NAMES

DEFAULTS = Path(__file__).parent / "defaults"
""" Directory holding the default format, themes and logo """

SOURCE = "_source"
""" Key added to each definition giving the file it came from, to report errors against """

BASE_THEME = "default"
""" Name of the built-in theme that every theme takes its missing values from, unless it extends another """

BASE_KEY = "__base__"
""" Where the built-in base theme is kept while resolving, so a user theme called "default" still has it to fall back on """

FORMAT_KEYS = {"title", "kicker", "generated", "theme_label", "default_theme", "builtin_themes", "logo", "css", "task_unit", "stale_days"}
THEME_KEYS = {"name", "label", "extends", "dark", "variables", "chart", "bars", "css"}
LOGO_KEYS = {"file", "svg", "alt", "link", "tooltip", "height"}
RAMP_KEYS = {"hue", "saturation", "lightness"}

CHART_KEYS = {
    "paper": "paper_bgcolor",
    "plot": "plot_bgcolor",
    "font": "font.color",
    "font_family": "font.family",
    "grid_x": "xaxis.gridcolor",
    "grid_y": "yaxis.gridcolor",
    "line": ("xaxis.linecolor", "yaxis.linecolor"),
    "legend_bg": "legend.bgcolor",
    "legend_border": "legend.bordercolor",
}
""" Chart colours a theme can set, and the plotly layout properties they set """

IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
               ".webp": "image/webp", ".svg": "image/svg+xml"}
""" Image files that can be used as a logo """

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_VARIABLE = re.compile(r"[a-z0-9][a-z0-9-]*")


@dataclass
class Theme:
    """ A fully resolved theme """

    name : str
    label : str
    dark : bool
    variables : dict[str, str]
    chart : dict[str, str]
    bars : dict
    css : str


@dataclass
class Format:
    """ The resolved format of the report """

    title : str
    kicker : str
    generated : str
    theme_label : str
    default_theme : str
    logo : str
    logo_link : str | None
    logo_tooltip : str
    logo_height : int
    css : str
    task_unit : str = "md"
    """ Unit of a task estimate, spent or remaining effort given as a number with no unit """
    stale_days : int | None = 14
    """ Days an unfinished task can go without a status update before it is stale. None turns the check off """
    themes : list[Theme] = field(default_factory=list)
    drawn_chart : dict[str, str] = field(default_factory=dict)
    """ Chart colours of the built-in default theme, which are the colours the charts are drawn in """


def _fail(source, message : str):
    raise ValueError(f"{source}: {message}")


def _check_keys(item : dict, allowed : set, what : str) -> None:
    unexpected = sorted(str(k) for k in item if k not in allowed and k != SOURCE)
    if unexpected:
        _fail(item.get(SOURCE), f"{what} has unexpected fields: {', '.join(repr(u) for u in unexpected)}. "
                                f"Expected fields are: {', '.join(sorted(allowed))}")


def _css_value(source, what : str, value) -> str:
    """ A value that is safe to write into a style sheet """

    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        _fail(source, f"{what} must be text, not {value!r}")
    value = str(value).strip()
    if not value or any(c in value for c in "{}<>"):
        _fail(source, f"{what} must not be empty or contain any of {{ }} < >, got {value!r}")
    return value


def _css_block(source, what : str, value) -> str:
    """ A block of CSS """

    if value is None:
        return ""
    if not isinstance(value, str):
        _fail(source, f"{what} must be text")
    if re.search(r"</\s*style", value, re.IGNORECASE):
        _fail(source, f"{what} must not contain </style")
    return value


def _load(path : Path) -> list[dict]:
    """ Read one of the yaml files of defaults and return its definitions """

    with open(path, encoding="utf-8") as f:
        content = yaml.safe_load(f)
    data = content["data"]
    items = data if isinstance(data, list) else [data]
    return [{**d, SOURCE : path} for d in items]


def defaults() -> tuple[list[dict], list[dict]]:
    """
    The format and themes that come with the tool

    :return: (format definitions, theme definitions)
    """

    return _load(DEFAULTS / "format.yaml"), _load(DEFAULTS / "themes.yaml")


def _logo(spec, source) -> tuple[str, str | None, str, int]:
    """
    Build the logo

    :return: (html of the image, link, tooltip, height)
    """

    if spec is None:
        return "", None, "", 44

    if not isinstance(spec, dict):
        _fail(source, "logo must be a mapping with 'file' or 'svg', or null for no logo")
    _check_keys({**spec, SOURCE : source}, LOGO_KEYS, "logo")

    if ("file" in spec) == ("svg" in spec):
        _fail(source, "logo must give exactly one of 'file' and 'svg'")

    alt = _html.escape(str(spec.get("alt", "logo")), quote=True)
    height = spec.get("height", 44)
    if isinstance(height, bool) or not isinstance(height, int) or not 8 <= height <= 300:
        _fail(source, f"logo height must be a whole number of pixels from 8 to 300, got {height!r}")

    link = spec.get("link")
    if link is not None and not isinstance(link, str):
        _fail(source, "logo link must be text")

    if "svg" in spec:
        svg = spec["svg"]
        if not isinstance(svg, str) or "<svg" not in svg:
            _fail(source, "logo svg must be svg markup")
        # svg has no alt attribute, so name it for screen readers the way an image would be
        image = f'<span role="img" aria-label="{alt}">{svg.strip()}</span>'
    else:
        file = spec["file"]
        if not isinstance(file, str):
            _fail(source, "logo file must be a path")
        path = (Path(source).parent / file)
        mime = IMAGE_TYPES.get(path.suffix.lower())
        if mime is None:
            _fail(source, f"logo file {file!r} must be one of {', '.join(IMAGE_TYPES)}")
        if not path.is_file():
            _fail(source, f"logo file {str(path)!r} does not exist")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        image = f'<img src="data:{mime};base64,{encoded}" alt="{alt}">'

    return image, link, str(spec.get("tooltip", "")), height


def _resolve_bars(bars, source, theme : str) -> dict:
    what = f"theme {theme!r} bars"

    if bars is None or bars == "original":
        return {"mode" : "original"}

    if isinstance(bars, list):
        if not bars:
            _fail(source, f"{what} palette must not be empty")
        return {"mode" : "palette", "palette" : [_css_value(source, f"{what} colour", c) for c in bars]}

    if isinstance(bars, dict) and set(bars) == {"ramp"} and isinstance(bars["ramp"], dict):
        ramp = bars["ramp"]
        _check_keys({**ramp, SOURCE : source}, RAMP_KEYS, f"{what} ramp")
        hue, saturation, light = ramp.get("hue", 0), ramp.get("saturation", 0), ramp.get("lightness", [20, 80])

        def number(n):
            return isinstance(n, (int, float)) and not isinstance(n, bool)

        valid_light = isinstance(light, list) and len(light) == 2 and all(map(number, light)) and 0 <= light[0] <= light[1] <= 100
        if not (number(hue) and number(saturation) and valid_light):
            _fail(source, f"{what} ramp needs numeric hue and saturation and lightness as [low, high] within 0 to 100")
        return {"mode" : "ramp", "hue" : hue, "saturation" : saturation, "lightness" : light}

    _fail(source, f"{what} must be 'original', a list of colours or a 'ramp'")


def _resolve_theme(name : str, raw : dict[str, dict], done : dict[str, Theme], stack : tuple = ()) -> Theme:
    """ Fill in the values a theme does not give from the theme it extends """

    if name in done:
        return done[name]

    item = raw[name]
    source = item[SOURCE]
    if name in stack:
        _fail(source, f"themes extend each other in a loop: {' -> '.join(stack + (name,))}")

    parent_name = item.get("extends", None if name == BASE_KEY else BASE_KEY)
    if parent_name is None:
        parent = None
    else:
        if parent_name not in raw:
            _fail(source, f"theme {name!r} extends {parent_name!r}, which is not a theme")
        parent = _resolve_theme(parent_name, raw, done, stack + (name,))

    variables = dict(parent.variables) if parent else {}
    chart = dict(parent.chart) if parent else {}

    for what, target in (("variables", variables), ("chart", chart)):
        given = item.get(what) or {}
        if not isinstance(given, dict):
            _fail(source, f"theme {name!r} {what} must be a mapping")
        for k, v in given.items():
            if what == "variables" and not _VARIABLE.fullmatch(str(k)):
                _fail(source, f"theme {name!r} variable {k!r} must be lower case letters, numbers and '-'")
            if what == "chart" and k not in CHART_KEYS:
                _fail(source, f"theme {name!r} has an unexpected chart colour {k!r}. Expected one of: {', '.join(CHART_KEYS)}")
            target[str(k)] = _css_value(source, f"theme {name!r} {what} {k!r}", v)

    dark = item.get("dark", parent.dark if parent else False)
    if not isinstance(dark, bool):
        _fail(source, f"theme {name!r} dark must be true or false")

    label = item.get("label", name)
    if not isinstance(label, str) or not label.strip():
        _fail(source, f"theme {name!r} label must be text")

    bars = _resolve_bars(item["bars"], source, name) if "bars" in item else (parent.bars if parent else {"mode" : "original"})

    theme = Theme(name, label.strip(), dark, variables, chart, bars, _css_block(source, f"theme {name!r} css", item.get("css")))
    done[name] = theme
    return theme


def configure(formats : list[dict], themes : list[dict]) -> Format:
    """
    Combine the defaults with what the user gave

    :param formats: format definitions from the input, later ones override earlier ones
    :param themes: theme definitions from the input. One with the name of a built-in theme replaces it
    :return: the format to use for the report
    """

    default_format, default_themes = defaults()

    # Format: later definitions change only the keys they give. Remember which file gave each, to report errors against
    merged, sources = {}, {}
    for item in default_format + formats:
        if not isinstance(item, dict):
            _fail(None, "format_definitions data must be a mapping")
        _check_keys(item, FORMAT_KEYS, "format")
        for k, v in item.items():
            if k != SOURCE:
                merged[k], sources[k] = v, item[SOURCE]

    for key in ("title", "kicker", "generated", "theme_label", "default_theme"):
        if not isinstance(merged[key], str):
            _fail(sources[key], f"{key} must be text")
    if not isinstance(merged["builtin_themes"], bool):
        _fail(sources["builtin_themes"], "builtin_themes must be true or false")
    task_unit = merged["task_unit"]
    if not isinstance(task_unit, str) or task_unit.strip().lower() not in EFFORT_UNITS:
        _fail(sources["task_unit"], f"task_unit {task_unit!r} is not one of: "
                                    + ", ".join(f"{u} ({n})" for u, n in UNIT_NAMES.items()))
    stale_days = merged["stale_days"]
    if stale_days is not None and (isinstance(stale_days, bool) or not isinstance(stale_days, int) or stale_days < 1):
        _fail(sources["stale_days"], f"stale_days must be a whole number of days, 1 or more, or null to turn the check off, "
                                     f"got {stale_days!r}")

    # Themes: the built-in base theme is always kept, since the others take their missing values from it
    raw = {BASE_KEY : next(t for t in default_themes if t["name"] == BASE_THEME)}
    if merged["builtin_themes"]:
        for t in default_themes:
            raw[t["name"]] = t
    offered = [n for n in raw if n != BASE_KEY]
    given = set()

    for t in themes:
        if not isinstance(t, dict):
            _fail(None, "themes_definitions data must be a list of themes")
        _check_keys(t, THEME_KEYS, "theme")
        name = t.get("name")
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            _fail(t[SOURCE], f"theme name must be letters, numbers, '-' and '_', got {name!r}")
        if name in given:
            _fail(t[SOURCE], f"theme {name!r} is defined more than once")
        given.add(name)
        raw[name] = t
        if name not in offered:
            offered.append(name)

    if not offered:
        _fail(sources["builtin_themes"], "there are no themes to offer: give themes_definitions or set builtin_themes to true")

    done = {}
    resolved = [_resolve_theme(n, raw, done) for n in offered]

    if merged["default_theme"] not in offered:
        _fail(sources["default_theme"], f"default_theme {merged['default_theme']!r} is not one of the themes: {', '.join(offered)}")

    image, link, tooltip, height = _logo(merged["logo"], sources["logo"])

    return Format(
        title=merged["title"].strip(),
        kicker=merged["kicker"].strip(),
        generated=merged["generated"],
        theme_label=merged["theme_label"],
        default_theme=merged["default_theme"],
        logo=image,
        logo_link=link,
        logo_tooltip=tooltip,
        logo_height=height,
        css=_css_block(sources["css"], "css", merged["css"]),
        task_unit=task_unit.strip().lower(),
        stale_days=stale_days,
        themes=resolved,
        drawn_chart=_resolve_theme(BASE_KEY, raw, done).chart,
    )


def theme_css(fmt : Format) -> str:
    """ CSS defining every theme, written as custom properties on the html element """

    default = next(t for t in fmt.themes if t.name == fmt.default_theme)

    def block(selector : str, t : Theme) -> str:
        lines = [f"    --{k}: {v};" for k, v in t.variables.items()]
        if t.dark:
            lines.append("    color-scheme: dark;")
        return selector + " {\n" + "\n".join(lines) + "\n}\n"

    css = block(":root", default)
    for t in fmt.themes:
        selector = f'html[data-theme="{t.name}"]'
        css += block(selector, t)
        css += t.css.replace("@theme", selector) + "\n"
    return css


def chart_themes(fmt : Format) -> dict:
    """
    What the page script needs to restyle the charts for each theme. "restyle" is false for a theme whose
    charts look as they are drawn, so the page need not redraw them when it opens in that theme
    """

    out = {}
    for t in fmt.themes:
        relayout = {}
        for key, value in t.chart.items():
            targets = CHART_KEYS[key]
            for target in (targets if isinstance(targets, tuple) else (targets,)):
                relayout[target] = value
        restyle = t.chart != fmt.drawn_chart or t.bars["mode"] != "original"
        out[t.name] = {"layout" : relayout, "bars" : t.bars, "restyle" : restyle}
    return out


_active : Format | None = None


def use(fmt : Format) -> None:
    """ Set the format used for every page of the report """

    global _active
    _active = fmt


def active() -> Format:
    """ The format used for every page of the report: the defaults unless use() has been called """

    global _active
    if _active is None:
        _active = configure([], [])
    return _active

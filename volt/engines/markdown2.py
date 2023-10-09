"""Markdown engine based on markdown2."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from copy import deepcopy
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime as dt
from functools import cached_property
from pathlib import Path
from typing import cast, Any, Callable, Generator, Optional, Self, Sequence
from urllib.parse import urljoin

import pendulum
import yaml
from jinja2 import Template
from markdown2 import Markdown
from pendulum.datetime import DateTime
from slugify import slugify
from yaml import SafeLoader

from .common import Engine
from .. import constants, error as err
from ..config import Config
from ..outputs import TemplateOutput


__all__ = ["MarkdownEngine", "MarkdownSource"]


class MarkdownEngine(Engine):

    """Engine that creates HTML outputs using the markdown2 library."""

    default_extras = {
        "fenced-code-blocks": {
            "nowrap": False,
            "full": False,
            "title": "",
            "noclasses": False,
            "classprefix": "",
            "cssclass": "hl",
            "csstyles": "",
            "prestyles": "",
            "cssfile": "",
            "noclobber_cssfile": False,
            "linenos": False,
            "hl_lines": [],
            "linenostart": 1,
            "linenostep": 1,
            "linenospecial": 0,
            "nobackground": False,
            "lineseparator": "\n",
            "lineanchors": "",
            "anchorlinenos": False,
        },
        "markdown-in-html": True,
        "header-ids": True,
        "footnotes": True,
    }

    @staticmethod
    def get_source_paths(
        base_dir: Path,
        recursive: bool = False,
        ext: str = constants.MARKDOWN_EXT,
    ) -> Generator[Path, None, None]:
        pattern = f"*{ext}"
        if recursive:
            return base_dir.rglob(pattern)
        return base_dir.glob(pattern)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        template_name = self.opts.pop("template_name", "page.html.j2")
        try:
            self.template = self.theme.load_template_file(template_name)
        except err.VoltMissingTemplateError:
            default_fp = Path(__file__).parent / "defaults" / f"{template_name}"
            self.template = Template(default_fp.read_text())

        self.extras = self.opts.pop("extras", None)

    def prepare_outputs(self, with_draft: bool) -> Sequence[TemplateOutput]:
        src_dirs = [self.config.contents_dir]
        if with_draft:
            src_dirs.append(self.config.draft_contents_dir)

        return [
            src.to_template_output(self.template)
            for src_dir in src_dirs
            for src in self.read_sources(src_dir)
        ]

    def read_sources(
        self,
        base_dir: Path,
        recursive: bool = False,
    ) -> Sequence["MarkdownSource"]:
        return [
            MarkdownSource.from_path(
                path=fp,
                config=self.config,
                converter=self.converter,
            )
            for fp in self.get_source_paths(base_dir)
        ]

    @cached_property
    def converter(self) -> Callable[[str], str]:
        resolved_extras = _resolve_extras(self.extras, self.default_extras)

        kwargs: dict = {}
        if isinstance((fd := resolved_extras.get("footnotes", None)), dict):
            for k in ("footnote_return_symbol", "footnote_title"):
                if (v := fd.get(k)) is not None:
                    kwargs[k] = v

        return cast(
            Callable[[str], str], Markdown(extras=resolved_extras, **kwargs).convert
        )


@dataclass(kw_only=True, eq=False)
class MarkdownSource:

    """A markdown input parsed using the markdown2 library."""

    # FileSystem path to the file content.
    path: Path

    # Metadata of the content.
    meta: dict

    # Site configuration.
    config: Config

    # Whether the content is draft or not.
    is_draft: bool

    # Markdown text of the body, without any metadata.
    body: str

    # Markdown converter.
    converter: Callable[[str], str]

    @classmethod
    def from_path(
        cls,
        path: Path,
        config: Config,
        converter: Callable[[str], str],
        meta: Optional[dict] = None,
        fm_sep: str = constants.FRONT_MATTER_SEP,
    ) -> Self:
        """Create an instance from a file.

        :param src: Path to the source file.
        :param config: Site configuration.
        :param meta: Optional metadata to inject.
        :param fm_sep: String for separating the markdown front matter.

        ."""
        raw_text = path.read_text()
        *top, raw_body = raw_text.split(fm_sep, 2)
        raw_fm = [item for item in top if item]
        fm = {} if not raw_fm else yaml.load(raw_fm[0].strip(), Loader=SafeLoader)

        return cls(
            body=raw_body,
            path=path,
            # TODO: Validate minimal front matter metadata.
            meta={**fm, **(meta or {})},
            config=config,
            is_draft=f"{path}".startswith(f"{config.draft_contents_dir}"),
            converter=converter,
        )

    @cached_property
    def url(self) -> str:
        config = self.config
        url_key = "url"
        title_key = "title"

        parts: list[str] = [f"{self._slugify(self.path.stem)}.html"]

        if (meta_url := self.meta.get(url_key)) is not None:
            parts = [part for part in meta_url.split("/") if part]

        elif (meta_title := self.meta.get(title_key)) is not None:
            parts = [f"{self._slugify(meta_title)}.html"]

        ps = [*(self.path.parent.parts[config.num_common_parts :]), *parts]
        if self.is_draft:
            with suppress(IndexError):
                # NOTE: This assumes that the `draft` folder is located at the same
                #       level as non-draft files.
                del ps[-2]

        return f"/{'/'.join(ps)}"

    @property
    def url_abs(self) -> str:
        return urljoin(self.config.url, self.url)

    @property
    def title(self) -> Optional[str]:
        return self.meta.get("title")

    @cached_property
    def pub_time(self) -> Optional[DateTime]:
        value = self.meta.get("pub_time", None)
        exc = err.VoltResourceError(
            f"value {value!r} in {str(self.path)!r} is not a valid datetime"
        )
        if value is None:
            return value
        if isinstance(value, str):
            rv = pendulum.parse(value)
            if isinstance(rv, DateTime):
                return rv
            raise exc
        if isinstance(value, dt):
            return pendulum.instance(value)
        raise exc

    @cached_property
    def html(self) -> str:
        return self.converter(self.body)

    def to_template_output(self, template: Template) -> TemplateOutput:
        """Create a :class:`TemplateOutput` instance."""

        return TemplateOutput(
            url=self.url,
            template=template,
            render_kwargs={
                "meta": {**self.meta, "url": self.url},
                "content": self.html,
            },
            src=self.path.relative_to(self.config.project_dir),
        )

    def _slugify(self, value: str) -> str:
        return slugify(value, replacements=self.config.slug_replacements)


def _resolve_extras(extras: Optional[dict], default_extras: dict) -> dict:
    resolved = deepcopy(default_extras)
    extras = extras or {}

    for k, v in extras.items():
        if v is False:
            resolved.pop(k, None)
        else:
            resolved[k] = v

    return resolved

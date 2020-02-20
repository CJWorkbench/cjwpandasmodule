# -*- coding: utf-8 -*-
import os
import pathlib
import re
from io import BytesIO
from typing import Any, Dict, Generator, List, Tuple

from babel.messages.catalog import Catalog, Message
from babel.messages.extract import (
    check_and_call_extract_file,
    extract_from_dir,
    extract_python,
)
from babel.messages.pofile import read_po, write_po

_default_message_re = re.compile(r"\s*default-message:\s*(.*)\s*")


default_locale_id = "en"
supported_locale_ids = ["en", "el"]
ROOT_DIR = pathlib.Path(os.path.abspath(__file__)).parent.parent / "cjwpandasmodule"


def _extract_python(
    fileobj: BytesIO, _keywords: Any, _comment_tags: Any, options: Dict[Any, Any]
) -> Generator[Tuple[int, str, List[Any], List[str]], None, None]:
    """Extract messages from project python code.
    
    :param fileobj: the seekable, file-like object the messages should be
                    extracted from
    :param _keywords: Ignored
    :param _comment_tags: Ignored
    :param options: a dictionary of additional options (optional)
    :rtype: ``iterator``
    """
    keywords = ["_trans_cjwpandasmodule"]
    comment_tags = ["i18n"]
    for (message_lineno, funcname, messages, translator_comments) in extract_python(
        fileobj, keywords, comment_tags, options
    ):
        # `messages` will have all the string parameters to our function
        # As we specify in the documentation of `trans`,
        # the first will be the message ID, the second will be the default message
        if len(messages) > 1 and messages[1]:
            # If we have a default, add it as a special comment
            # that will be processed by our `merge_catalogs` script
            translator_comments.append(
                (message_lineno, "default-message: " + messages[1])
            )

        # Pybabel expects a `funcname` of the `gettext` family, or `None`.
        funcname = None

        yield (
            message_lineno,
            funcname,
            messages[0],
            [comment[1] for comment in translator_comments],
        )


def catalog_path(locale_id: str) -> pathlib.Path:
    return pathlib.Path(ROOT_DIR) / "i18n" / f"{locale_id}.po"


def extract_to_pot_catalog() -> Tuple[Catalog, Dict[str, str]]:

    mappings = [(ROOT_DIR, [("**.py", _extract_python)], {})]
    pot_catalog = Catalog(default_locale_id)

    for path, method_map, options_map in mappings:

        def callback(filename, method, options):
            if method == "ignore":
                return

        if os.path.isfile(path):
            current_dir = os.getcwd()
            extracted = check_and_call_extract_file(
                path, method_map, options_map, callback, {}, [], False, current_dir
            )
        else:
            extracted = extract_from_dir(
                path,
                method_map,
                options_map,
                keywords={},
                comment_tags=[],
                callback=callback,
                strip_comment_tags=False,
            )
        for filename, lineno, message, comments, context in extracted:
            if os.path.isfile(path):
                filepath = filename  # already normalized
            else:
                filepath = os.path.normpath(os.path.join(path, filename))

            pot_catalog.add(
                message,
                None,
                [(os.path.relpath(filepath, ROOT_DIR), lineno)],
                auto_comments=comments,
                context=context,
            )

    default_messages = {}
    for message in pot_catalog:
        if message.id:
            actual_comments = []
            for comment in message.auto_comments:
                match = re.match(_default_message_re, comment)
                if match:
                    default_message = match.group(1).strip()
                    default_messages[message.id] = default_message
                else:
                    actual_comments.append(comment)
            message.auto_comments = actual_comments

    return pot_catalog, default_messages


def extract():
    pot_catalog, default_messages = extract_to_pot_catalog()
    catalog = _update_catalog(default_locale_id, pot_catalog, default_messages)
    write_po_catalog(default_locale_id, catalog)
    for locale_id in supported_locale_ids:
        if locale_id != default_locale_id:
            catalog = _update_catalog(locale_id, pot_catalog, {})
            write_po_catalog(locale_id, catalog)


def check():
    pot_catalog, default_messages = extract_to_pot_catalog()
    catalog = _update_catalog(default_locale_id, pot_catalog, default_messages)
    check_catalog(default_locale_id, catalog)
    for locale_id in supported_locale_ids:
        if locale_id != default_locale_id:
            catalog = _update_catalog(locale_id, pot_catalog, {})
            check_catalog(locale_id, catalog)


def _update_catalog(
    locale_id: str, pot_catalog: Catalog, default_messages: Dict[str, str]
) -> Catalog:
    try:
        with open(catalog_path(locale_id), "rb") as po:
            catalog = read_po(po)
    except FileNotFoundError:
        catalog = Catalog(locale_id)

    to_delete = [
        message.id
        for message in catalog
        if message.id and message.id not in pot_catalog
    ]
    for message_id in to_delete:
        print(
            "Deleting message %r! Unsure whether this is correct? git reset --hard"
            % message_id
        )
        catalog.delete(message_id)

    for message in pot_catalog:
        if message.id:
            old_message = catalog.get(message.id)
            new_string = default_messages.get(
                message.id, old_message.string if old_message else ""
            )
            if old_message:
                catalog.delete(message.id)
            catalog.add(
                message.id,
                string=new_string,
                auto_comments=message.auto_comments,
                user_comments=message.user_comments,
                flags=message.flags,
                locations=message.locations,
            )

    return catalog


def write_po_catalog(locale_id: str, catalog: Catalog):
    with open(catalog_path(locale_id), "wb") as po_file:
        write_po(po_file, catalog)


def check_catalog(locale_id: str, catalog: Catalog):
    try:
        with open(catalog_path(locale_id), "rb") as po:
            old_catalog = read_po(po)
    except FileNotFoundError:
        old_catalog = Catalog(locale_id)

    assert_catalogs_are_same(catalog, old_catalog)


def assert_catalogs_are_same(catalog_1: Catalog, catalog_2: Catalog):
    assert (
        catalog_1.locale == catalog_2.locale
    ), "Catalogs have different locales: %s, %s" % (catalog_1.locale, catalog_2.locale)
    assert_catalog_inclusion(catalog_1, catalog_2)
    assert_catalog_inclusion(catalog_2, catalog_1)


def assert_catalog_inclusion(catalog: Catalog, other_catalog: Catalog):
    for message in catalog:
        if message.id:  # ignore header
            other_message = other_catalog.get(message.id)
            assert other_message, (
                "Message %s is not contained in both catalogs" % message.id
            )
            assert_messages_are_same(message, other_message)


def assert_messages_are_same(message: Message, other_message: Message):
    assert message.id == other_message.id, "Messages have different ids: %s, %s" % (
        message.id,
        other_message.id,
    )
    assert message.string == other_message.string, (
        "Messages with id %s have different string: %s, %s"
        % (message.id, message.string, other_message.string)
    )
    assert message.flags == other_message.flags, (
        "Messages with id %s have different flags: %s, %s"
        % (message.id, message.flags, other_message.flags)
    )
    assert message.auto_comments == other_message.auto_comments, (
        "Messages with id %s have different auto_comments: %s, %s"
        % (message.id, message.auto_comments, other_message.auto_comments)
    )
    assert message.user_comments == other_message.user_comments, (
        "Messages with id %s have different user_comments: %s, %s"
        % (message.id, message.user_comments, other_message.user_comments)
    )
    assert message.locations == other_message.locations, (
        "Messages with id %s have different locations: %s, %s"
        % (message.id, message.locations, other_message.locations)
    )

# -*- coding: utf-8 -*-
import importlib
import logging
import pkgutil
from collections.abc import Mapping

from .config_structures import ConfigValueError, SetupError


def get_modules_by_name_prefix(prefix):
    """Get modules whose name starts with the prefix.

    :param prefix: a prefix used to select modules to be returned.
    :returns: a map of the modules to their names, with the prefix
        stripped.
    """
    logger = logging.getLogger(__name__)

    name_module_map = {}
    for _, module_name, _ in pkgutil.iter_modules():
        if not module_name.startswith(prefix):
            continue
        try:
            module = importlib.import_module(module_name)
            name_module_map[module_name[len(prefix):]] = module
            logger.info('Successfully imported "%s" module.', module_name)
        except ImportError:
            logger.exception(
                'A module "%s" was found, but couldn\'t be imported',
                module_name
            )

    return name_module_map


def apply_configured_plugins(obj, available_plugins):
    """Apply configured plugins to the object.

    :param obj: an object to which the function applies available
        plugins. It also provides the configuration that includes a
        plugin section as a mapping of names of plugins to activate to
        configuration options to be used by each plugin.
    :param available_plugins: a map of available plugins to their names.
    :raises ConfigValueError: if an unavailable plugin is included in
        the configuration, or if this error was raised while applying
        a plugin.
    :raises SetupError: if there was an error with setting up a plugin.
    """
    logger = logging.getLogger(__name__)
    plugin_config = obj.config['plugins']
    if not isinstance(plugin_config, Mapping):
        raise ConfigValueError('Invalid plugin configuration format.')

    for name in plugin_config:
        logger.info('Attemtping to initialize "%s" plugin...')
        try:
            module = available_plugins[name]
        except KeyError:
            raise ConfigValueError(
                'The "{}" plugin is configured but not available.'.format(name)
            )
        try:
            module.apply_to(obj)
        except SetupError as e:
            raise SetupError(
                'Error while setting up "{}" plugin.'.format(name)
            ) from e
        logger.info('The "%s" plugin was successfully initialized.', name)

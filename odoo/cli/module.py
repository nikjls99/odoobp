import logging
import textwrap
from contextlib import contextmanager
from pathlib import Path

import odoo
from odoo.cli.command import Command
from odoo.modules.loading import force_demo
from odoo.modules.module import get_module_path, initialize_sys_path
from odoo.modules.registry import Registry
from odoo.tools import config

_logger = logging.getLogger(__name__)


class Module(Command):
    """ Install, Upgrade, Uninstall modules, install demo data """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subparsers = self.parser.add_subparsers(
            dest='subcommand', required=True,
            help='Subcommands help')

        self.force_demo_parser = subparsers.add_parser(
            'force-demo',
            help="Install demo data (force)",
            description="Install demonstration data (force)",
        )
        self.install_parser = subparsers.add_parser(
            'install',
            help="Install modules",
            description="Install selected modules",
        )
        self.upgrade_parser = subparsers.add_parser(
            'upgrade',
            help="Upgrade modules",
            description="Upgrade selected modules",
        )
        self.uninstall_parser = subparsers.add_parser(
            'uninstall',
            help="Uninstall modules",
            description="Uninstall selected modules",
        )

        for parser in (
            self.install_parser,
            self.uninstall_parser,
            self.force_demo_parser,
            self.upgrade_parser,
        ):
            parser.add_argument(
                '-c', '--config', dest='config',
                help="use a specific configuration file")
            parser.add_argument(
                '-d', '--database', dest='db_name', default=None,
                help="database name, connection details will be taken from the config file")

        self.install_parser.add_argument(
            'modules', nargs='+', metavar='MODULE',
            help="modules to be installed")
        self.install_parser.epilog = textwrap.dedent("""\
            Before installing modules, an Odoo database needs
            to be created and initialized on your PostgreSQL
            instance, using the `db create` command:

            $ odoo-bin db create <db_name>

            To get help on its parameters, see:

            $ odoo-bin db create --help
        """)
        self.uninstall_parser.add_argument(
            'modules', nargs='+', metavar='MODULE',
            help="modules to be uninstalled")
        self.upgrade_parser.add_argument(
            'modules', nargs='+', metavar='MODULE',
            help="modules to be upgraded")

    def run(self, cmdargs):
        parsed_args = self.parser.parse_args(args=cmdargs)

        config_args = []
        if parsed_args.config:
            config_args += ['-c', parsed_args.config]
        if parsed_args.db_name:
            config_args += ['-d', parsed_args.db_name]
        config.parse_config(config_args, setup_logging=True)

        db_names = config['db_name']
        if not db_names or len(db_names) > 1:
            self.parser.error("Please provide a single database in the config file")
        parsed_args.db_name = db_names[0]
        if 'modules' in parsed_args and parsed_args.subcommand in ('install', 'upgrade'):
            parsed_args.modules = self._get_module_names(parsed_args.modules)

        match parsed_args.subcommand:
            case 'install':
                self._install(parsed_args)
            case 'uninstall':
                self._uninstall(parsed_args)
            case 'upgrade':
                self._upgrade(parsed_args)
            case 'force-demo':
                self._force_demo(parsed_args)

    def _get_zip_path(self, path):
        if (
            (fullpath := Path(path).resolve())
            and fullpath.exists()
            and fullpath.suffix.lower() == '.zip'
        ):
            return fullpath
        return None

    def _get_module_names(self, module_names):
        """ Get valid module names from disk before starting the Db environment """
        initialize_sys_path()
        module_names = set(module_names)
        valid_module_names = {
            module
            for module in module_names
            if get_module_path(module)
            or self._get_zip_path(module)
        }
        if not valid_module_names:
            _logger.warning("No valid module names found")
        return valid_module_names

    def _get_modules(self, env, module_names):
        """ Get modules from the db, depending on the state """
        Module = env['ir.module.module']
        Module.update_list()
        return Module.search([('name', 'in', module_names)])

    @contextmanager
    def _create_env_context(self, db_name):
        with Registry.new(db_name).cursor() as cr:
            yield odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    def _install(self, parsed_args):
        with self._create_env_context(parsed_args.db_name) as env:

            installable_modules = self._get_modules(env, parsed_args.modules)
            parsed_args.modules = set(parsed_args.modules) - set(installable_modules.mapped("name"))
            if installable_modules:
                installable_modules.button_immediate_install()

            importable_zipfiles = {
                fullpath
                for module in parsed_args.modules
                if (fullpath := self._get_zip_path(module))
            }
            if 'imported' not in env['ir.module.module']._fields:
                _logger.warning("Cannot import data modules unless the `base_import_module` module is installed")
            else:
                for importable_zipfile in importable_zipfiles:
                    env['ir.module.module']._import_zipfile(importable_zipfile)

    def _upgrade(self, parsed_args):
        with self._create_env_context(parsed_args.db_name) as env:
            if modules := self._get_modules(env, parsed_args.modules):
                modules.button_immediate_upgrade()

    def _uninstall(self, parsed_args):
        with self._create_env_context(parsed_args.db_name) as env:
            if modules := self._get_modules(env, parsed_args.modules):
                modules.button_immediate_uninstall()

    def _force_demo(self, parsed_args):
        with self._create_env_context(parsed_args.db_name) as env:
            force_demo(env)

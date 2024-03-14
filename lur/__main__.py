from jinja2 import FileSystemLoader, Environment
import argparse
import functools
import yaml
from typing import Callable, Optional
import time
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('lur')


def parse_cli_args():
    parser = argparse.ArgumentParser(
        prog='filename',
        description='name of template file',
    )

    parser.add_argument('filename')
    parser.add_argument('-o', default='main.yaml', dest='dest_filename')
    return parser.parse_args()


class TplFixer:

    @staticmethod
    def _no_fixer(f):
        return f

    @staticmethod
    def _simple_rule_fixer(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            res = f(*args, **kwargs).split('\n')
            if len(res) == 1:
                return res[0]
            fixed_res = [res[0][2:]] + res[1:]
            return '\n  '.join(fixed_res)
        return wrapper


    @staticmethod
    def get_fixer(macros_name: str) -> Optional[Callable[[Callable], Callable]]:
        if macros_name[0] == '_':
            return None
        if macros_name.startswith('rule_'):
            return TplFixer._simple_rule_fixer
        return TplFixer._no_fixer


class EnvironmentConstructor:
    _env: Environment

    def __init__(self):
        fs_loader = FileSystemLoader(['manifests', 'rules', 'rules_groups'])
        self._env = Environment(
            loader=fs_loader,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @staticmethod
    def _filter_macros_tpl(filename):
        return filename.split('.', 1)[1] in {'tpl.yaml', 'tpl.yml'}

    @staticmethod
    def _get_macros_kv_for_build(env: Environment):
        for tpl_name in env.list_templates(filter_func=EnvironmentConstructor._filter_macros_tpl):
            for name, macros in env.get_template(tpl_name).module.__dict__.items():
                yield name, macros

    def construct(self) -> Environment:
        for name, macros in self._get_macros_kv_for_build(self._env):
            fixer = TplFixer.get_fixer(name)
            if fixer is None:
                continue
            self._env.globals.update({name: fixer(macros)})
        return self._env


class Merger:
    def __init__(self):
        self._env = EnvironmentConstructor().construct()

    def merge(self, filename):
        generated_config = self._env.get_template(filename).render()
        yaml_content = yaml.safe_load(generated_config)
        yaml_content['rules'] = list(self._build_rules(filename))
        return yaml_content

    def _build_rules(self, filename, template_params=None):
        if template_params is None:
            template_params = dict()
        generated_config = self._env.get_template(filename).render(**template_params)
        yaml_content = yaml.safe_load(generated_config)
        for rule_obj in yaml_content['rules']:
            if 'include' in rule_obj:
                new_template_params = rule_obj.copy()
                new_template_params.pop('include')
                yield from self._build_rules(rule_obj['include'], new_template_params)
            else:
                yield rule_obj


class Checker:
    @staticmethod
    def _check_rule_unique_name(configuration):
        rules = configuration['rules']

        names_counter = Counter(map(lambda x: x['name'], rules))
        non_unique_names = []
        for name, count in names_counter.items():
            if count > 1:
                non_unique_names.append(name)
        if len(non_unique_names) > 0:
            log.error('Non unique rule names: %s', ', '.join(non_unique_names))

    @staticmethod
    def check(configuration):
        Checker._check_rule_unique_name(configuration)


def main():
    log.info('Merging started')
    start = time.time()
    cli_args = parse_cli_args()
    merged_configuration = Merger().merge(cli_args.filename)
    Checker.check(merged_configuration)

    with open(cli_args.dest_filename, 'w') as f:
        yaml.dump(merged_configuration, f)
    finish = time.time()
    log.info(f'Configuration built for %.2f s', finish - start)


if __name__ == '__main__':
    main()

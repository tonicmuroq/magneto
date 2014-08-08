# coding: utf-8

from jinja2 import Environment, PackageLoader

import magneto


class Jinja2(object):

    def __init__(self, package_name, template_folder='templates'):
        self.loader = PackageLoader(package_name, template_folder)
        self.environment = Environment(loader=self.loader, autoescape=True)

    def render_template(self, template_name, **data):
        template = self.environment.get_template(template_name)
        return template.render(**data)


template = Jinja2(magneto.__name__)

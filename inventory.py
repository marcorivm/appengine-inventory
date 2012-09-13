import jinja2
import os
import cgi
import datetime
import urllib
import webapp2

from google.appengine.ext import db

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class Product(db.Model):
    description = db.StringProperty()
    stock = db.IntegerProperty()


def inventory_key(inventory_name=None):
    """Construye un Datastore key para un inventario utlizando inventory_name"""
    return db.Key.from_path('Inventory', inventory_name or 'default_inventory')


class MainPage(webapp2.RequestHandler):
    def get(self):

        products = Product.gql('WHERE ANCESTOR IS :1 ORDER BY stock DESC', inventory_key())

        template_values = {
            'products': products
        }

        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))


class Edit(webapp2.RequestHandler):
    def get(self):
        product_name = self.request.get('product')
        if product_name == 'new':
            product = Product(parent=inventory_key())
            is_new = True
        else:
            try:
                product = Product.get_by_key_name(product_name, parent=inventory_key())
                is_new = False
            except db.BadKeyError:
                product = Product()
                is_new = True

        template_values = {
            'product': product,
            'is_new': is_new,
            'has_errors': self.request.get('error', False)
        }
        template = jinja_environment.get_template('edit.html')
        self.response.out.write(template.render(template_values))


class Save(webapp2.RequestHandler):
    def post(self):
            has_errors = False
            product_name = self.request.get('product')
            if product_name == 'new':
                product_code = self.request.get('product_code')
                if len(product_code) == 10:
                    product = Product.get_by_key_name(product_code, parent=inventory_key())
                    if product == None:
                        has_errors = False
                        product = Product(parent=inventory_key(), key_name=product_code)
                    else:
                        has_errors = True
                else:
                    product = Product()
                    has_errors = True
            else:
                try:
                    product = Product.get_by_key_name(product_name, parent=inventory_key())
                except db.BadKeyError:
                    product = Product()
                    has_errors = True

            try:
                product.description = self.request.get('description')
                has_errors = True if len(product.description) > 255 else has_errors
            except db.BadValueError:
                has_errors = True

            try:
                product.stock = int(self.request.get('stock'))
            except ValueError:
                has_errors = True

            if has_errors:
                self.redirect('/edit?' + urllib.urlencode({'product': product_name, 'error': has_errors}))
            else:
                product.put()
                self.redirect('/?' + urllib.urlencode({'success': True}))


class Delete(webapp2.RequestHandler):
    def post(self):
            product_name = self.request.get('product')
            has_errors = False
            try:
                product = Product.get_by_key_name(product_name, parent=inventory_key())
            except db.BadKeyError:
                has_errors = True
            if not has_errors:
                product.delete()


app = webapp2.WSGIApplication([('/', MainPage), ('/edit', Edit), ('/save', Save), ('/delete', Delete)], debug=True)

import frappe
from frappe.website.doctype.website_settings.website_settings import get_website_settings
from frappe.website.page_controllers.web_page import WebPage
from frappe.website.website_components.metatags import MetaTags


class BaseTemplatePage(WebPage):
	def init_context(self):
		self.context = frappe._dict()
		self.context.update(get_website_settings())
		self.context.update(frappe.local.conf.get("website_context") or {})

	def add_csrf_token(self, html):
		if frappe.local.session:
			csrf_token = frappe.local.session.data.csrf_token
			return html.replace("<!-- csrf_token -->",
				f'<script>frappe.csrf_token = "{csrf_token}";</script>')

		return html

	def post_process_context(self):
		self.tags = MetaTags(self.path, self.context).tags
		self.context.metatags = self.tags
		self.set_base_template_if_missing()
		self.set_title_with_prefix()
		self.update_website_context()

		# set using frappe.respond_as_web_page
		if hasattr(frappe.local, 'response') and frappe.local.response.get('context'):
			self.context.update(frappe.local.response.context)

		# to be able to inspect the context dict
		# Use the macro "inspect" from macros.html
		self.context._context_dict = self.context
		self.context.canonical = frappe.utils.get_url(frappe.utils.escape_html(self.path))

		# context sends us a new template path
		if self.context.template:
			self.template_path = self.context.template

	def set_base_template_if_missing(self):
		if not self.context.base_template_path:
			app_base = frappe.get_hooks("base_template")
			self.context.base_template_path = app_base[-1] if app_base else "templates/base.html"

	def set_title_with_prefix(self):
		if (self.context.title_prefix and self.context.title
			and not self.context.title.startswith(self.context.title_prefix)):
			self.context.title = '{0} - {1}'.format(self.context.title_prefix, self.context.title)

	def update_website_context(self):
		# apply context from hooks
		update_website_context = frappe.get_hooks('update_website_context')
		for method in update_website_context:
			values = frappe.get_attr(method)(self.context)
			if values:
				self.context.update(values)

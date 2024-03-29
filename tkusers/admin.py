from django.apps import apps
from django.contrib import admin
from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import autodiscover_modules
from .models import TurkuADGroupMapping

if hasattr(settings, 'SITE_TYPE'):
    if settings.SITE_TYPE not in ('dev', 'test', 'production'):
        raise ImproperlyConfigured("SITE_TYPE must be either 'dev', 'test' or 'production'")


PROVIDERS = (
    ('tkusers.providers.turku', 'turku_login'),
    ('tkusers.providers.turku_oidc', 'turku_oidc_login')
)


class AdminSite(admin.AdminSite):
    login_template = "admin/tku_login.html"

    def __init__(self, *args, **kwargs):
        super(AdminSite, self).__init__(*args, **kwargs)
    
    @property
    def site_header(self):
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            Site = apps.get_model(app_label='sites', model_name='Site')
            site = Site.objects.get_current()
            site_name = site.name
        elif hasattr(settings, 'WAGTAIL_SITE_NAME'):
            site_name = settings.WAGTAIL_SITE_NAME
        else:
            return ugettext_lazy("Django admin")
        return ugettext_lazy("%(site_name)s admin") % {'site_name': site_name}

    def each_context(self, request):
        ret = super(AdminSite, self).each_context(request)
        ret['site_type'] = getattr(settings, 'SITE_TYPE', 'dev')
        ret['redirect_path'] = request.GET.get('next', None)
        provider_installed = False
        if 'tkusers.tunnistamo_oidc.TunnistamoOIDCAuth' in settings.AUTHENTICATION_BACKENDS:
            provider_installed = True
            login_url = reverse('social:begin', kwargs=dict(backend='tunnistamo'))
        else:
            for provider, login_view in PROVIDERS:
                if provider not in settings.INSTALLED_APPS:
                    continue
                provider_installed = True
                login_url = reverse(login_view)
                break

        ret['turku_provider_installed'] = provider_installed
        if provider_installed:
            ret['turku_login_url'] = login_url

        ret['grappelli_installed'] = 'grappelli' in settings.INSTALLED_APPS
        if ret['grappelli_installed']:
            ret['grappelli_admin_title'] = self.site_header
            ret['base_site_template'] = 'admin/base_site_grappelli.html'
        else:
            ret['base_site_template'] = 'admin/base_site_default.html'

        ret['password_login_disabled'] = getattr(settings, 'TKUSERS_PASSWORD_LOGIN_DISABLED', False)

        return ret

site = AdminSite()
site._registry.update(admin.site._registry)
default_admin_site = admin.site

admin.site = site
admin.sites.site = site


def autodiscover():
    autodiscover_modules('admin', register_to=site)
    site._registry.update(default_admin_site._registry)


class TurkuADGroupMappingAdmin(admin.ModelAdmin):
    pass
site.register(TurkuADGroupMapping, TurkuADGroupMappingAdmin)
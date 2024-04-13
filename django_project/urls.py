from importlib import import_module

from allauth.socialaccount import providers
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from player.views import HomePageView

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('account/', include('accounts.urls')),
                  path('player/', include('player.urls')),
                  path('reviews/api/v1/', include('reviews.urls')),
                  path('', HomePageView.as_view(), name='home')
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


provider_urlpatterns = []
provider_classes = providers.registry.get_class_list()

provider_classes = [cls for cls in provider_classes if cls.id != "openid_connect"] + [
    cls for cls in provider_classes if cls.id == "openid_connect"
]
for provider_class in provider_classes:
    prov_mod = import_module(provider_class.get_package() + ".urls")
    prov_urlpatterns = getattr(prov_mod, "urlpatterns", None)
    if prov_urlpatterns:
        provider_urlpatterns += prov_urlpatterns

urlpatterns += provider_urlpatterns
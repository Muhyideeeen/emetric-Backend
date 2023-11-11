from django.conf import settings
from django_tenants.middleware import TenantSubfolderMiddleware
from django_tenants.utils import has_multi_type_tenants, get_public_schema_name


class CustomTenantSubFolderMiddleware(TenantSubfolderMiddleware):
    @staticmethod
    def setup_url_routing(request, force_public=False):
        """
        Sets the correct url conf based on the tenant
        :param request:
        :param force_public:
        :return:
        """
        if has_multi_type_tenants():
            return TenantSubfolderMiddleware.setup_url_routing(
                request, force_public=force_public
            )

        # Do we have a public-specific urlconf?
        if hasattr(settings, "PUBLIC_SCHEMA_URLCONF") and (
            force_public
            or (not hasattr(request, "tenant"))
            or request.tenant.schema_name == get_public_schema_name()
        ):
            request.urlconf = settings.PUBLIC_SCHEMA_URLCONF

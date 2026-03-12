from django.utils.deprecation import MiddlewareMixin

from apps.core_users.models import UserProfile
from .models import Company, Membership


class ActiveCompanyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.active_company = None
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return

        try:
            profile = getattr(user, "erp_profile", None)
        except UserProfile.DoesNotExist:
            profile = None
        session_company_id = request.session.get("active_company_id")

        if session_company_id:
            try:
                company = Company.objects.get(id=session_company_id, is_active=True)
            except Company.DoesNotExist:
                company = None
            if company and Membership.objects.filter(user=user, company=company, status="active").exists():
                request.active_company = company
                if profile and profile.active_company_id != company.id:
                    profile.active_company = company
                    profile.save(update_fields=["active_company"])
                return

        if profile and profile.active_company and profile.active_company.is_active:
            request.active_company = profile.active_company

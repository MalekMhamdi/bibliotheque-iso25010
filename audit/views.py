from django.views.generic import ListView

from audit.models import JournalAudit
from comptes.permissions import RoleRequisMixin


class AuditListe(RoleRequisMixin, ListView):
    roles_autorises = ("ADMIN",)
    model = JournalAudit
    template_name = "audit/audit_liste.html"
    context_object_name = "entrees"
    paginate_by = 20
    queryset = JournalAudit.objects.select_related("utilisateur")
# Create your views here.

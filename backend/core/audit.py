from core.models import AuditLog


def write_audit(*, actor, family, action, instance, before=None, after=None):
    if family is None:
        return
    AuditLog.objects.create(
        actor=actor,
        family=family,
        action=action,
        model=instance.__class__.__name__,
        object_id=str(instance.pk),
        before=before,
        after=after,
    )

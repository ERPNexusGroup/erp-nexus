# apps/core_payments/tasks.py
"""
Celery tasks para Payout Automation.
- process_payout_batch: envía batch de payouts a SRI/banco
- reconcile_payouts_daily: reconcilia pagos procesados con confirmación bancaria
- schedule_pending_payouts: agrupa comisiones pendientes y crea payouts
- send_payout_confirmed_email: notifica a usuario que su pago fue confirmado
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta

from celery import shared_task, Task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from ..models import Payout, Commission, BankAccount, PayoutSchedule

logger = get_task_logger(__name__)


class BasePayoutTask(Task):
    """Base task con retry configurado."""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_jitter = True


@shared_task(bind=True, base=BasePayoutTask, queue='payments')
def process_payout_batch(self, payout_ids: list[str]):
    """
    Procesa batch de payouts (enviándolos a SRI/banco).
    Actualiza status: PENDING → PROCESSING → PAID/FAILED
    """
    logger.info(f"Procesando batch de {len(payout_ids)} payouts")
    payouts = Payout.objects.filter(id__in=payout_ids).select_related('bank_account', 'commission__user')
    failed = []

    for payout in payouts:
        try:
            if payout.status != Payout.Status.PENDING:
                logger.warning(f"Payout {payout.id} no está PENDING, saltando")
                continue

            from .integrations.sri import SRIClient

            client = SRIClient(
                cert_path=settings.SRI_CERT_PATH,
                cert_password=settings.SRI_CERT_PASSWORD,
                environment=settings.SRI_ENVIRONMENT,
            )

            result = client.create_transfer(
                bank_account=payout.bank_account,
                amount=float(payout.amount),
                reference=str(payout.id),
            )

            if result.get('success'):
                payout.status = Payout.Status.PROCESSING
                payout.provider_response = result
                payout.save(update_fields=['status', 'provider_response', 'updated_at'])
                logger.info(f"Payout {payout.id} enviado a SRI (txn_id={result.get('transaction_id')})")
            else:
                payout.status = Payout.Status.FAILED
                payout.error_message = result.get('error', 'Error desconocido')
                payout.save(update_fields=['status', 'error_message', 'updated_at'])
                failed.append(str(payout.id))
                logger.error(f"Payout {payout.id} falló: {payout.error_message}")

        except Exception as exc:
            logger.exception(f"Error procesando payout {payout.id}: {exc}")
            payout.status = Payout.Status.FAILED
            payout.error_message = str(exc)
            payout.save(update_fields=['status', 'error_message', 'updated_at'])
            failed.append(str(payout.id))
            # Retry individual
            self.retry(exc=exc, countdown=120)

    if failed:
        send_payout_batch_failed_email.delay(failed)
    return {'processed': len(payout_ids), 'failed': len(failed)}


@shared_task(queue='payments', cron='0 6 * * *')  # 6am diario
def reconcile_payouts_daily():
    """
    Revisa payouts en PROCESSING y consulta estado real en SRI/banco.
    Actualiza a PAID si confirmado, o FAILED si rechazado.
    """
    logger.info("Iniciando reconciliación diaria de payouts")
    processing = Payout.objects.filter(status=Payout.Status.PROCESSING)
    updated = 0

    from .integrations.sri import SRIClient
    client = SRIClient(
        cert_path=settings.SRI_CERT_PATH,
        cert_password=settings.SRI_CERT_PASSWORD,
        environment=settings.SRI_ENVIRONMENT,
    )

    for payout in processing:
        try:
            txn_id = payout.provider_response.get('transaction_id') if payout.provider_response else None
            if not txn_id:
                continue

            status_result = client.query_status(transaction_id=txn_id)
            if status_result.get('confirmed'):
                payout.status = Payout.Status.PAID
                payout.paid_at = timezone.now()
                payout.save(update_fields=['status', 'paid_at', 'updated_at'])
                # Actualizar comisión
                payout.commission.status = Commission.Status.PAID
                payout.commission.paid_at = timezone.now()
                payout.commission.save(update_fields=['status', 'paid_at', 'updated_at'])
                updated += 1
                logger.info(f"Payout {payout.id} confirmado como PAID")
                # Notificar usuario
                send_payout_confirmed_email.delay(str(payout.id))
            elif status_result.get('rejected'):
                payout.status = Payout.Status.FAILED
                payout.error_message = status_result.get('reason', 'Rechazado por banco')
                payout.save(update_fields=['status', 'error_message', 'updated_at'])
                logger.warning(f"Payout {payout.id} rechazado: {payout.error_message}")

        except Exception as exc:
            logger.exception(f"Error reconciliando payout {payout.id}: {exc}")

    return {'reconciled': processing.count(), 'updated_to_paid': updated}


@shared_task(queue='payments', cron='*/15 * * * *')  # cada 15min
def schedule_pending_payouts():
    """
    Agrupa comisiones PENDING por usuario y crea Payouts pendientes de envío.
    Solo si el usuario tiene BankAccount verificada y monto >= min_payout_amount.
    """
    logger.info("Buscando comisiones pendientes para crear payouts")
    from django.db.models import Sum

    # Group by user, sum amounts
    pending_commissions = Commission.objects.filter(
        status=Commission.Status.PENDING,
        payout__isnull=True,
        user__bank_accounts__is_verified=True,
    ).select_related('user')

    # Agrupar por usuario
    from collections import defaultdict
    by_user = defaultdict(list)
    for c in pending_commissions:
        by_user[c.user_id].append(c)

    created_count = 0
    for user_id, commissions in by_user.items():
        total = sum(c.amount for c in commissions)
        # Buscar schedule del usuario
        schedule = PayoutSchedule.objects.filter(user_id=user_id, is_active=True).first()
        min_amount = schedule.min_payout_amount if schedule else 10.00

        if total < min_amount:
            logger.info(f"Usuario {user_id}: monto {total} < min {min_amount}, saltando")
            continue

        # Obtener bank account default
        bank = BankAccount.objects.filter(user_id=user_id, is_default=True, is_verified=True).first()
        if not bank:
            logger.warning(f"Usuario {user_id}: sin bank account default verificada")
            continue

        # Crear Payout agrupado (vinculando solo primera comisión como "lead")
        with transaction.atomic():
            payout = Payout.objects.create(
                commission=commissions[0],  # lead commission
                bank_account=bank,
                amount=total,
                currency=commissions[0].currency,
                status=Payout.Status.PENDING,
                provider=Payout.Provider.SRI,
            )
            # Marcar resto de comisiones como asociadas (TODO: si need many-to-many)
            # Por ahora solo la linked directa
            created_count += 1
            logger.info(f"Creado Payout {payout.id} para usuario {user_id} — monto {total}")

    return {'payouts_created': created_count, 'users_processed': len(by_user)}


@shared_task(queue='payments')
def send_payout_confirmed_email(payout_id: str):
    """Envía email de confirmación de pago al usuario."""
    try:
        payout = Payout.objects.select_related('commission__user', 'bank_account').get(id=payout_id)
        user = payout.commission.user
        subject = f"[ERP Nexus] Pago confirmado — {payout.amount} {payout.currency}"
        context = {
            'user': user,
            'payout': payout,
            'bank_name': payout.bank_account.bank_name,
            'account_masked': '****' + payout.bank_account.account_number[-4:],
        }
        body = render_to_string('emails/payout_confirmed.txt', context)
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        logger.info(f"Email de confirmación enviado a {user.email} para payout {payout_id}")
    except Exception as exc:
        logger.exception(f"Error enviando email de payout {payout_id}: {exc}")


@shared_task(queue='payments')
def send_payout_batch_failed_email(payout_ids: list[str]):
    """Notifica a admin sobre batch de payouts fallido."""
    failed = Payout.objects.filter(id__in=payout_ids).select_related('commission__user')
    subject = f"[ERP Nexus] ⚠️ Batch de pagos falló — {len(failed)} transacciones"
    body = f"""El batch de pagos automáticos falló para {len(failed)} transacciones:

Payouts fallidos:
"""
    for p in failed:
        body += f"  - {p.id} | {p.commission.user.email} | {p.amount} | Error: {p.error_message or 'Unknown'}\n"

    body += "\nRevisar logs y reintentar manualmente."
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_ALERT_EMAIL], fail_silently=True)

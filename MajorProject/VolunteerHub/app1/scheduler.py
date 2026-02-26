# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from .models import Service, Application


def send_service_reminders():

    print("⏰ Checking 1-day reminders...")
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    print("Today:", today)
    print("Tomorrow:", tomorrow)


    services = Service.objects.filter(
        start_date=tomorrow,
        reminder_sent=False
    )

    print("Services starting tomorrow:", services.count())

    for service in services:

        selected_apps = Application.objects.filter(
            service=service,
            status="SELECTED"
        ).select_related("volunteer__user")

        # 🔥 Collect all coordinators
        coordinators = service.coordinators

        coordinator_text = ""

        for c in coordinators:
            coordinator_text += f"\n• {c['name']} - {c['phone']}"

        if not coordinator_text:
            coordinator_text = "\nNo coordinator assigned."

        for app in selected_apps:

            volunteer = app.volunteer.user

            from django.core.mail import EmailMultiAlternatives
            from django.utils.html import strip_tags

            for app in selected_apps:

                volunteer = app.volunteer.user

                # Build coordinator list HTML
                coordinator_html = ""
                for c in coordinators:
                    coordinator_html += f"""
                    <tr>
                        <td style="padding:6px 0;">
                            👤 <strong>{c['name']}</strong><br>
                            📞 {c['phone']}
                        </td>
                    </tr>
                    """

                if not coordinator_html:
                    coordinator_html = """
                    <tr>
                        <td>No coordinator assigned.</td>
                    </tr>
                    """

                subject = f"Reminder: {service.title} Starts Tomorrow"

                html_content = f"""
                <!DOCTYPE html>
                <html>
                <body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">

                <table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f4f6f9">
                    <tr>
                        <td align="center">

                            <table width="600" cellpadding="0" cellspacing="0"
                                   style="background:#ffffff;margin:40px 0;border-radius:12px;
                                          overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.08);">

                                <!-- HEADER -->
                                <tr>
                                    <td style="background:linear-gradient(90deg,#22c55e,#16a34a);
                                               padding:25px;text-align:center;color:#ffffff;">
                                        <h2 style="margin:0;">VolunteerHub</h2>
                                        <p style="margin:5px 0 0;">Service Reminder</p>
                                    </td>
                                </tr>

                                <!-- BODY -->
                                <tr>
                                    <td style="padding:30px;color:#333333;">

                                        <h3>Hello {volunteer.username},</h3>

                                        <p>
                                            This is a friendly reminder that your upcoming service
                                            is scheduled for tomorrow.
                                        </p>

                                        <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">

                                        <table width="100%" cellpadding="0" cellspacing="0"
                                               style="font-size:15px;">
                                            <tr>
                                                <td><strong>Service Title:</strong></td>
                                                <td>{service.title}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Location:</strong></td>
                                                <td>{service.location}</td>
                                            </tr>
                                            <tr>
                                                <td><strong>Date:</strong></td>
                                                <td>{service.start_date}</td>
                                            </tr>
                                        </table>

                                        <hr style="border:none;border-top:1px solid #e5e7eb;margin:25px 0;">

                                        <h4>📞 Coordinators</h4>
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            {coordinator_html}
                                        </table>

                                        <hr style="border:none;border-top:1px solid #e5e7eb;margin:25px 0;">

                                        <h4>📋 Important Instructions</h4>
                                        <ul style="padding-left:20px;">
                                            <li>Arrive at least 15 minutes early</li>
                                            <li>Carry your ID card</li>
                                            <li>Follow all coordinator instructions</li>
                                            <li>If unable to attend, inform coordinator immediately</li>
                                        </ul>

                                        <p style="margin-top:30px;">
                                            We appreciate your commitment to making a difference.
                                        </p>

                                        <p>
                                            Regards,<br>
                                            <strong>VolunteerHub Team</strong>
                                        </p>

                                    </td>
                                </tr>

                                <!-- FOOTER -->
                                <tr>
                                    <td style="background:#f9fafb;padding:15px;
                                               text-align:center;font-size:12px;color:#777;">
                                        © 2026 VolunteerHub. All rights reserved.
                                    </td>
                                </tr>

                            </table>

                        </td>
                    </tr>
                </table>

                </body>
                </html>
                """

                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(
                    subject,
                    text_content,
                    "noreply@volunteerhub.com",
                    [volunteer.email],
                )

                email.attach_alternative(html_content, "text/html")
                email.send()

            print("✅ Reminder sent to:", volunteer.email)

        # Mark reminder as sent
        service.reminder_sent = True
        service.save()

        print("✔ Reminder flag updated for:", service.title)


def start():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        send_service_reminders,
        trigger='cron',
        hour=9,      # 9 AM
        minute=0
    )
    scheduler.start()
    print("🚀 Scheduler started (Daily 9 AM)")
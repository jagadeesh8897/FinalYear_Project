from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def generate_breadcrumbs(context):
    request = context['request']
    path = request.path.strip('/')
    parts = path.split('/')

    breadcrumbs = []
    url = ""

    for part in parts:
        url += "/" + part

        name = part.replace('-', ' ').replace('_', ' ').title()

        # ===== CUSTOM MAPPINGS =====

        if part == "organization":
            breadcrumbs.append(("Organization", reverse("organization_dashboard")))

        elif part == "volunteer":
            breadcrumbs.append(("Volunteer", reverse("volunteer_dashboard")))

        elif part == "admin_panel":
            breadcrumbs.append(("Admin Panel", reverse("admin_dashboard")))

        elif part == "service" or part.isdigit():
            breadcrumbs.append(("", reverse("organization_dashboard")))


        else:
            breadcrumbs.append((name, url + "/"))

    return breadcrumbs
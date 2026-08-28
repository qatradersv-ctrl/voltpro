from django.core.management.base import BaseCommand
from core.models import Project, Service

PROJECTS = [
    dict(
        title="Solar Installation for Industrial Warehouse",
        location="Industrial Area, Nairobi",
        summary="50kW grid-tie solar system with battery backup for a manufacturing facility.",
        completed_on="2026-06-15",
        order=1,
    ),
    dict(
        title="Commercial Building Wiring",
        location="Westlands, Nairobi",
        summary="Complete electrical wiring for a 5-story commercial office building.",
        completed_on="2026-05-20",
        order=2,
    ),
    dict(
        title="Access Control System Installation",
        location="Upper Hill, Nairobi",
        summary="Biometric access control system for a corporate office with 500+ employees.",
        completed_on="2026-07-10",
        order=3,
    ),
    dict(
        title="Electric Gate Automation",
        location="Karen, Nairobi",
        summary="Motorized sliding gate installation with safety sensors and remote control.",
        completed_on="2026-04-25",
        order=4,
    ),
    dict(
        title="CCTV Security System",
        location="Nairobi CBD",
        summary="32-camera CCTV system with NVR and remote viewing capabilities.",
        completed_on="2026-06-30",
        order=5,
    ),
    dict(
        title="Backup Power Installation",
        location="Mombasa Road, Nairobi",
        summary="UPS and generator installation for data center with automatic transfer switch.",
        completed_on="2026-03-15",
        order=6,
    ),
]


class Command(BaseCommand):
    help = "Seed VoltPro Electrodata Solutions projects."

    def handle(self, *args, **options):
        created, updated = 0, 0
        services = Service.objects.all()
        
        for i, data in enumerate(PROJECTS):
            # Create a copy of data to avoid modifying the original
            project_data = data.copy()
            
            # Assign a random service to each project
            if services.exists():
                service = services[i % services.count()]
                project_data["service"] = service
            
            obj, was_created = Project.objects.update_or_create(
                title=project_data["title"], defaults=project_data
            )
            created += was_created
            updated += not was_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Projects: {created} created, {updated} updated."
            )
        )

from django.core.management.base import BaseCommand
from core.models import Service, Testimonial, ServiceCategory as C

SERVICES = [
    dict(
        title="Solar Power Installation",
        slug="solar-installation",
        category=C.SOLAR,
        icon="sun",
        rating_note="Grid-tie & off-grid",
        short_description="Panels, inverters and sizing built around your actual load, not a catalogue default.",
        description=(
            "We survey your roof and your bill before we quote a panel. Every solar system "
            "is sized against your real consumption, then installed with proper isolation, "
            "earthing and inverter configuration so it holds up through Nairobi's rain and "
            "sun in the same week. Grid-tie, hybrid and full off-grid builds, all commissioned "
            "with a load test before we hand you the keys."
        ),
    ),
    dict(
        title="Electrical Installation & Repair",
        slug="electrical-installation",
        category=C.INFRA,
        icon="bolt",
        rating_note="Single & 3-phase",
        short_description="Fault-finding, rewiring and new circuits done to code, not to guesswork.",
        description=(
            "General electrical work for homes, offices and industrial floors — new circuits, "
            "fault diagnosis, DB board upgrades, and repairs on installations other contractors "
            "left half-done. Every job is tested and certified before we close it out."
        ),
    ),
    dict(
        title="Building Wiring",
        slug="building-wiring",
        category=C.INFRA,
        icon="building",
        rating_note="New builds & rewires",
        short_description="First-fix to final-fix wiring for new construction and full rewires.",
        description=(
            "Complete electrical wiring for buildings under construction and rewires for older "
            "properties — conduit runs, DB layout, socket and lighting circuits, and coordination "
            "with your architect's electrical plan so nothing gets buried behind a wall twice."
        ),
    ),
    dict(
        title="UPS & Clean Power Installation",
        slug="ups-clean-power",
        category=C.POWER,
        icon="shield-bolt",
        rating_note="Surge & sag protection",
        short_description="Keeps sensitive equipment running clean through spikes, sags and outages.",
        description=(
            "UPS sizing and installation for server rooms, control panels and equipment that "
            "can't tolerate a dirty supply — with proper battery banks, bypass switching and "
            "load testing so failover actually works when the grid drops."
        ),
    ),
    dict(
        title="Battery & Power Backup Systems",
        slug="battery-backup",
        category=C.POWER,
        icon="battery",
        rating_note="Lithium & lead-acid",
        short_description="Battery banks sized to your outage pattern, not an oversized sales quote.",
        description=(
            "Standalone and solar-paired battery backup installations, sized against how long "
            "and how often you actually lose power — including charge controller setup, "
            "battery monitoring and safe enclosure builds."
        ),
    ),
    dict(
        title="Fingerprint Door Access Control",
        slug="fingerprint-access-control",
        category=C.ACCESS,
        icon="fingerprint",
        rating_note="Biometric & card",
        short_description="Biometric access on doors, gates and server rooms with full audit logs.",
        description=(
            "Fingerprint and card-based access control for offices, gates and restricted rooms — "
            "wired into electric strikes or maglocks, with user enrolment and access logs so you "
            "know exactly who went where and when."
        ),
    ),
    dict(
        title="Generator Installation & Repair",
        slug="generator-installation-repair",
        category=C.POWER,
        icon="generator",
        rating_note="ATS changeover",
        short_description="Standby power installed with automatic changeover, plus ongoing servicing.",
        description=(
            "Standby generator installation with automatic transfer switching, sound canopy "
            "siting, exhaust and fuel line work, plus repair and servicing contracts for "
            "generators already on site."
        ),
    ),
    dict(
        title="Electric Security Fencing",
        slug="security-fencing",
        category=C.ACCESS,
        icon="fence",
        rating_note="Perimeter alarm-linked",
        short_description="Perimeter fencing wired to an energiser and alarm, installed to spec.",
        description=(
            "Electric perimeter fencing installation with energiser, earthing and zone "
            "monitoring — built to withstand weather and tampering, with alarm output wired "
            "to your existing security system where one exists."
        ),
    ),
    dict(
        title="CCTV Installation",
        slug="cctv-installation",
        category=C.ACCESS,
        icon="camera",
        rating_note="IP & analogue, NVR/DVR",
        short_description="Camera placement planned for actual blind spots, not just corners.",
        description=(
            "CCTV design and installation — camera placement walked through with you on site, "
            "structured cabling back to the NVR, remote viewing setup, and footage retention "
            "configured to your storage budget."
        ),
    ),
    dict(
        title="Structured Network Cabling",
        slug="network-cabling",
        category=C.INFRA,
        icon="network",
        rating_note="Cat6 & fibre",
        short_description="Cat6 and fibre runs, patched, labelled and tested end to end.",
        description=(
            "Structured cabling for offices and industrial sites — Cat6/6A and fibre runs, "
            "patch panel termination, rack organisation and cable testing with certification "
            "reports for every run."
        ),
    ),
    dict(
        title="Control Panel Design & Fabrication",
        slug="control-panels",
        category=C.INFRA,
        icon="panel",
        rating_note="PLC & relay logic",
        short_description="Panels built and wired to schematic, labelled for the next technician.",
        description=(
            "Custom control panel design, fabrication and wiring for pumps, motors and process "
            "equipment — built to a documented single-line diagram, clearly labelled, and "
            "tested under load before commissioning."
        ),
    ),
    dict(
        title="Electric Sliding Gate Installation & Repair",
        slug="sliding-gate-installation-repair",
        category=C.GATES,
        icon="gate",
        rating_note="Motor & safety sensors",
        short_description="Motorised sliding gates with safety sensors, plus repair on existing units.",
        description=(
            "Sliding gate motor installation with safety edge sensors and remote/keypad "
            "control, plus diagnosis and repair of gates that are jamming, drifting off track "
            "or losing power to the motor."
        ),
    ),
    dict(
        title="Industrial & Commercial Switchgear",
        slug="industrial-switchgear",
        category=C.POWER,
        icon="switchgear",
        rating_note="LV panels & changeovers",
        short_description="LV switchgear supply, installation and changeover, built to spec.",
        description=(
            "Supply and installation of low-voltage switchgear, distribution boards and "
            "changeover panels for commercial and industrial sites, including load studies "
            "and coordination with your utility connection."
        ),
    ),
    dict(
        title="Solar Power Solutions",
        slug="solar-power-solutions",
        category=C.SOLAR,
        icon="sun",
        rating_note="Design, supply & install",
        short_description="Solar system design, supply, and installation for residential and commercial.",
        description=(
            "Comprehensive solar power solutions including system design, equipment supply, "
            "and professional installation. We handle grid-tie, hybrid, and off-grid systems "
            "tailored to your specific energy needs and site conditions."
        ),
    ),
    dict(
        title="Backup Power Solutions",
        slug="backup-power-solutions",
        category=C.POWER,
        icon="battery",
        rating_note="Alternative power systems",
        short_description="Backup and alternative power systems for uninterrupted operations.",
        description=(
            "Complete backup power solutions including generators, UPS systems, and battery "
            "banks. We design and install systems that ensure your operations continue during "
            "power outages and grid failures."
        ),
    ),
    dict(
        title="Electrical Wiring & Installations",
        slug="electrical-wiring-installations",
        category=C.INFRA,
        icon="bolt",
        rating_note="Design, wiring & loads",
        short_description="Electrical design, wiring, and load installations for all property types.",
        description=(
            "Professional electrical wiring and installation services covering design, load "
            "calculations, and complete wiring for residential, commercial, and industrial "
            "properties. All work done to code and certified."
        ),
    ),
    dict(
        title="Security Systems",
        slug="security-systems",
        category=C.ACCESS,
        icon="shield",
        rating_note="Integrated protection",
        short_description="Security installation and integrated protection solutions for premises.",
        description=(
            "Comprehensive security system installation including CCTV, alarm systems, and "
            "integrated protection solutions. We design systems that provide complete coverage "
            "and seamless integration with your existing infrastructure."
        ),
    ),
    dict(
        title="Access Control Systems",
        slug="access-control-systems",
        category=C.ACCESS,
        icon="fingerprint",
        rating_note="Entry management",
        short_description="Systems for controlling and managing entry to premises and facilities.",
        description=(
            "Advanced access control systems for managing entry to your premises. We install "
            "biometric, card-based, and keypad systems with full audit trails and integration "
            "capabilities for complete access management."
        ),
    ),
    dict(
        title="Gate Automation",
        slug="gate-automation",
        category=C.GATES,
        icon="gate",
        rating_note="Automated gate systems",
        short_description="Installation and setup of automated gates for residential and commercial.",
        description=(
            "Professional gate automation services including motor installation, safety sensor "
            "setup, and control system integration. We handle sliding, swinging, and barrier "
            "gate automation with remote access capabilities."
        ),
    ),
    dict(
        title="Power System Design",
        slug="power-system-design",
        category=C.POWER,
        icon="design",
        rating_note="SLD & electrical planning",
        short_description="Including single-line diagrams and electrical planning for projects.",
        description=(
            "Professional power system design services including single-line diagrams, load "
            "studies, and comprehensive electrical planning. We provide detailed designs "
            "that ensure safe, efficient, and code-compliant power distribution."
        ),
    ),
    dict(
        title="Site Surveys & Assessments",
        slug="site-surveys-assessments",
        category=C.INFRA,
        icon="clipboard",
        rating_note="Feasibility studies",
        short_description="Inspecting sites, existing power supply, loads, and project feasibility.",
        description=(
            "Comprehensive site surveys and assessments covering existing power supply, load "
            "analysis, and project feasibility studies. We provide detailed reports that "
            "inform accurate quoting and successful project execution."
        ),
    ),
    dict(
        title="Supply of Electrical & Security Equipment",
        slug="supply-electrical-security-equipment",
        category=C.POWER,
        icon="package",
        rating_note="Materials & equipment",
        short_description="Providing the required materials and equipment for installations.",
        description=(
            "Supply of high-quality electrical and security equipment for installations. We "
            "provide all necessary materials including cables, switchgear, security devices, "
            "and components to ensure project success."
        ),
    ),
]

TESTIMONIALS = [
    dict(
        client_name="M. Odhiambo",
        client_role="Facility Manager, Industrial Park, Nairobi",
        quote=(
            "They rewired our switchgear and installed the changeover panel over a single "
            "weekend shutdown. No comebacks, no surprises on the invoice."
        ),
        order=1,
    ),
    dict(
        client_name="J. Wanjiru",
        client_role="Homeowner, Karen",
        quote=(
            "Solar and battery backup sized to what we actually use — not the oversized "
            "package the last quote pushed on us."
        ),
        order=2,
    ),
    dict(
        client_name="A. Mutiso",
        client_role="Operations Lead, Warehouse, Athi River",
        quote=(
            "Fingerprint access and CCTV went in together, cabled properly the first time. "
            "Logs and footage both work exactly as briefed."
        ),
        order=3,
    ),
]


class Command(BaseCommand):
    help = "Seed VoltPro Electrodata Solutions services and testimonials."

    def handle(self, *args, **options):
        created, updated = 0, 0
        for i, data in enumerate(SERVICES):
            data["order"] = i
            obj, was_created = Service.objects.update_or_create(
                slug=data["slug"], defaults=data
            )
            created += was_created
            updated += not was_created

        for data in TESTIMONIALS:
            Testimonial.objects.update_or_create(
                client_name=data["client_name"], defaults=data
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Services: {created} created, {updated} updated. "
                f"Testimonials seeded: {len(TESTIMONIALS)}."
            )
        )

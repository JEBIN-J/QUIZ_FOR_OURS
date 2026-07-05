from django.core.management.base import BaseCommand
from quiz.models import Category


GOVERNMENT_CATEGORIES = [
    {
        'name': 'UPSC / IAS',
        'description': 'Union Public Service Commission — Indian Administrative Service. Prepare for Prelims, Mains and Interview rounds covering GS, CSAT and Optional subjects.',
        'icon': 'fa-landmark',
    },
    {
        'name': 'IPS',
        'description': 'Indian Police Service — Civil Services exam route for law enforcement leadership. Covers law, criminology, and public administration topics.',
        'icon': 'fa-shield-halved',
    },
    {
        'name': 'IFS',
        'description': 'Indian Foreign Service — Diplomatic cadre of the Civil Services. Focus on international relations, economics, and current affairs.',
        'icon': 'fa-earth-asia',
    },
    {
        'name': 'CISF',
        'description': 'Central Industrial Security Force — Paramilitary security force guarding industrial units, airports, and government buildings.',
        'icon': 'fa-user-shield',
    },
    {
        'name': 'CAPF',
        'description': 'Central Armed Police Forces — Includes BSF, CRPF, CISF, ITBP, SSB, NSG, and AR. UPSC CAPF AC exam preparation.',
        'icon': 'fa-helmet-safety',
    },
    {
        'name': 'BSF',
        'description': 'Border Security Force — India\'s primary border guarding organisation. Prepare for BSF Head Constable, SI, and ASI recruitment exams.',
        'icon': 'fa-flag',
    },
    {
        'name': 'Army',
        'description': 'Indian Army — Prepare for NDA, CDS, TES, AFCAT, Agniveer and other Army recruitment and officer exams.',
        'icon': 'fa-star',
    },
    {
        'name': 'Navy',
        'description': 'Indian Navy — Prepare for NDA, INET, AA/SSR, MR, Tradesman Mate and Officer entry recruitment exams.',
        'icon': 'fa-anchor',
    },
    {
        'name': 'Air Force',
        'description': 'Indian Air Force — Prepare for NDA, AFCAT, Agniveer Vayu, Group X & Y Airmen entry exams.',
        'icon': 'fa-jet-fighter',
    },
    {
        'name': 'SSC CGL',
        'description': 'Staff Selection Commission Combined Graduate Level — One of the most popular government exams for Group B & C posts.',
        'icon': 'fa-file-pen',
    },
    {
        'name': 'SSC CHSL',
        'description': 'Staff Selection Commission Combined Higher Secondary Level — For 10+2 pass candidates targeting LDC, DEO, and Postal Assistant posts.',
        'icon': 'fa-file-lines',
    },
    {
        'name': 'Railway (RRB)',
        'description': 'Railway Recruitment Board — RRB NTPC, Group D, ALP, JE exams for thousands of railway department vacancies.',
        'icon': 'fa-train',
    },
    {
        'name': 'Banking (IBPS/SBI)',
        'description': 'IBPS PO, IBPS Clerk, SBI PO, SBI Clerk, RRB PO/Clerk — Banking sector recruitment exams with quantitative and reasoning focus.',
        'icon': 'fa-building-columns',
    },
    {
        'name': 'General Knowledge',
        'description': 'Current Affairs, Indian History, Geography, Polity, Economics, and Science — Core GK topics required across all government exams.',
        'icon': 'fa-book-open',
    },
    {
        'name': 'Reasoning & Aptitude',
        'description': 'Logical reasoning, quantitative aptitude, verbal ability and data interpretation — essential for all competitive exam sections.',
        'icon': 'fa-brain',
    },
]


class Command(BaseCommand):
    help = 'Seeds government exam preparation categories into the database.'

    def handle(self, *args, **kwargs):
        created_count = 0
        updated_count = 0

        for cat_data in GOVERNMENT_CATEGORIES:
            obj, created = Category.objects.update_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✔ Created: {obj.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'  ↺ Updated: {obj.name}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! {created_count} categories created, {updated_count} updated.'
        ))

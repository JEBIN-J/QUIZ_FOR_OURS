from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quiz.models import Category, Subject, Quiz, Question, Choice

class Command(BaseCommand):
    help = 'Seeds government exam quizzes into the database.'

    def handle(self, *args, **kwargs):
        # Create a dummy admin user if not exists for 'created_by'
        admin, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'})
        if created:
            admin.set_password('admin123')
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        quizzes_data = [
            {
                "category_name": "UPSC / IAS",
                "title": "UPSC Prelims Mock Test 1 - General Studies",
                "description": "A comprehensive mock test covering History, Geography, Polity, and Economy.",
                "difficulty": "Hard",
                "duration": 120,
                "passing_score": 50,
                "questions": [
                    {
                        "text": "Which of the following Fundamental Rights is/are available to both citizens and foreigners?",
                        "options": [
                            {"text": "Right to equality before the law", "is_correct": True},
                            {"text": "Right against discrimination on grounds of religion, race, caste, sex or place of birth", "is_correct": False},
                            {"text": "Right to equal opportunity in matters of public employment", "is_correct": False},
                            {"text": "Right to freedom of speech and expression", "is_correct": False}
                        ],
                        "explanation": "Article 14 (Equality before law) is available to both citizens and foreigners."
                    },
                    {
                        "text": "With reference to the 'Cabinet Mission', which of the following statements is/are correct?",
                        "options": [
                            {"text": "It recommended a federal government.", "is_correct": True},
                            {"text": "It enlarged the powers of the Indian courts.", "is_correct": False},
                            {"text": "It provided for more Indians in the ICS.", "is_correct": False},
                            {"text": "All of the above", "is_correct": False}
                        ],
                        "explanation": "The Cabinet Mission (1946) recommended a weak federal government with provinces having autonomy."
                    }
                ]
            },
            {
                "category_name": "SSC CGL",
                "title": "SSC CGL Tier I - Quantitative Aptitude",
                "description": "Practice set for SSC CGL Tier I focused on math and quantitative reasoning.",
                "difficulty": "Medium",
                "duration": 60,
                "passing_score": 60,
                "questions": [
                    {
                        "text": "If A's salary is 20% less than B's salary, by how much percent is B's salary more than A's?",
                        "options": [
                            {"text": "20%", "is_correct": False},
                            {"text": "25%", "is_correct": True},
                            {"text": "30%", "is_correct": False},
                            {"text": "33.33%", "is_correct": False}
                        ],
                        "explanation": "Let B = 100, then A = 80. B is more than A by 20. Percent = (20/80)*100 = 25%."
                    },
                    {
                        "text": "A train 150m long is running at 72 km/hr. How long will it take to cross a platform 250m long?",
                        "options": [
                            {"text": "15 sec", "is_correct": False},
                            {"text": "18 sec", "is_correct": False},
                            {"text": "20 sec", "is_correct": True},
                            {"text": "25 sec", "is_correct": False}
                        ],
                        "explanation": "Speed = 72 * 5/18 = 20 m/s. Total distance = 150 + 250 = 400m. Time = 400/20 = 20 sec."
                    }
                ]
            },
            {
                "category_name": "Banking (IBPS/SBI)",
                "title": "IBPS PO Prelims - English Language",
                "description": "English language mock test for banking preliminary exams.",
                "difficulty": "Medium",
                "duration": 20,
                "passing_score": 50,
                "questions": [
                    {
                        "text": "Choose the synonym of 'OMNIPRESENT'.",
                        "options": [
                            {"text": "Ubiquitous", "is_correct": True},
                            {"text": "Powerful", "is_correct": False},
                            {"text": "Knowing everything", "is_correct": False},
                            {"text": "Merciful", "is_correct": False}
                        ],
                        "explanation": "Omnipresent means present everywhere, which is the exact meaning of ubiquitous."
                    },
                    {
                        "text": "Identify the grammatically correct sentence.",
                        "options": [
                            {"text": "One of the boy has done his work.", "is_correct": False},
                            {"text": "One of the boys has done his work.", "is_correct": True},
                            {"text": "One of the boy have done his work.", "is_correct": False},
                            {"text": "One of the boys have done his work.", "is_correct": False}
                        ],
                        "explanation": "The phrase 'One of the...' is followed by a plural noun and a singular verb."
                    }
                ]
            },
            {
                "category_name": "Army",
                "title": "NDA General Ability Test (GAT) Mock",
                "description": "General Knowledge and English test for National Defence Academy preparation.",
                "difficulty": "Medium",
                "duration": 150,
                "passing_score": 40,
                "questions": [
                    {
                        "text": "Who is the Supreme Commander of the Indian Armed Forces?",
                        "options": [
                            {"text": "Prime Minister", "is_correct": False},
                            {"text": "Chief of Defence Staff (CDS)", "is_correct": False},
                            {"text": "President of India", "is_correct": True},
                            {"text": "Minister of Defence", "is_correct": False}
                        ],
                        "explanation": "Under Article 53 of the Constitution, the supreme command of the Armed Forces is vested in the President."
                    },
                    {
                        "text": "The Equator does NOT pass through which of the following continents?",
                        "options": [
                            {"text": "Africa", "is_correct": False},
                            {"text": "South America", "is_correct": False},
                            {"text": "Asia", "is_correct": False},
                            {"text": "Europe", "is_correct": True}
                        ],
                        "explanation": "The Equator passes through South America, Africa, and Asia, but not Europe."
                    }
                ]
            },
            {
                "category_name": "Railway (RRB)",
                "title": "RRB NTPC CBT 1 - General Awareness",
                "description": "General Awareness practice set for Railway Non-Technical Popular Categories.",
                "difficulty": "Easy",
                "duration": 30,
                "passing_score": 60,
                "questions": [
                    {
                        "text": "Which is the longest railway platform in India (and the world)?",
                        "options": [
                            {"text": "Gorakhpur", "is_correct": False},
                            {"text": "Hubballi", "is_correct": True},
                            {"text": "Kharagpur", "is_correct": False},
                            {"text": "New Delhi", "is_correct": False}
                        ],
                        "explanation": "Shree Siddharoodha Swamiji Hubballi Station (Karnataka) has the longest platform (1505 meters)."
                    }
                ]
            }
        ]

        created_count = 0

        for q_data in quizzes_data:
            category_name = q_data["category_name"]
            
            # Fetch the category
            try:
                category = Category.objects.get(name=category_name)
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Category '{category_name}' not found. Skipping '{q_data['title']}'."))
                continue

            # Create a generic subject if none exists
            subject, _ = Subject.objects.get_or_create(
                name="General Practice",
                category=category
            )

            # Create or get Quiz
            quiz, created = Quiz.objects.get_or_create(
                title=q_data["title"],
                defaults={
                    "description": q_data["description"],
                    "category": category,
                    "subject": subject,
                    "difficulty": q_data["difficulty"],
                    "duration": q_data["duration"],
                    "passing_score": q_data["passing_score"],
                    "status": "Published",
                    "created_by": admin
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✔ Created Quiz: {quiz.title}"))

                # Add Questions and Choices
                for qst_data in q_data["questions"]:
                    question = Question.objects.create(
                        quiz=quiz,
                        text=qst_data["text"],
                        question_type="MCQ",
                        difficulty=q_data["difficulty"],
                        points=1,
                        explanation=qst_data["explanation"]
                    )
                    
                    for opt_data in qst_data["options"]:
                        Choice.objects.create(
                            question=question,
                            text=opt_data["text"],
                            is_correct=opt_data["is_correct"]
                        )
            else:
                self.stdout.write(self.style.NOTICE(f"  - Quiz already exists: {quiz.title}"))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Successfully added {created_count} quizzes.'))

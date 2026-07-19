with open('/Users/apple/Desktop/Quizz/quiz/views.py', 'r') as f:
    content = f.read()
    
new_content = content.replace('''        if not (form.is_valid() and section_formset.is_valid() and condition_formset.is_valid()):
            print("FORM ERRORS:", form.errors)
            print("SECTION ERRORS:", section_formset.errors)
            print("CONDITION ERRORS:", condition_formset.errors)
            print("SECTION NON FORM ERRORS:", section_formset.non_form_errors())''', '''        if not (form.is_valid() and section_formset.is_valid() and condition_formset.is_valid()):
            print("FORM ERRORS:", form.errors)
            print("SECTION ERRORS:", section_formset.errors)
            print("CONDITION ERRORS:", condition_formset.errors)
            print("SECTION NON FORM ERRORS:", section_formset.non_form_errors())
            if form.errors:
                messages.error(request, f"Form Errors: {form.errors}")
            if section_formset.errors and any(section_formset.errors):
                messages.error(request, f"Section Errors: {section_formset.errors}")
            if section_formset.non_form_errors():
                messages.error(request, f"Section Formset Errors: {section_formset.non_form_errors()}")''')

with open('/Users/apple/Desktop/Quizz/quiz/views.py', 'w') as f:
    f.write(new_content)

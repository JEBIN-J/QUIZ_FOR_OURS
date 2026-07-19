with open('/Users/apple/Desktop/Quizz/quiz/views.py', 'r') as f:
    content = f.read()
    
new_content = content.replace('''        if form.is_valid() and section_formset.is_valid() and condition_formset.is_valid():
        else:
            print("FORM ERRORS:", form.errors)
            print("SECTION ERRORS:", section_formset.errors)
            print("CONDITION ERRORS:", condition_formset.errors)
            print("SECTION NON FORM ERRORS:", section_formset.non_form_errors())
        if form.is_valid() and section_formset.is_valid() and condition_formset.is_valid():''', '''        if not (form.is_valid() and section_formset.is_valid() and condition_formset.is_valid()):
            print("FORM ERRORS:", form.errors)
            print("SECTION ERRORS:", section_formset.errors)
            print("CONDITION ERRORS:", condition_formset.errors)
            print("SECTION NON FORM ERRORS:", section_formset.non_form_errors())
            
        if form.is_valid() and section_formset.is_valid() and condition_formset.is_valid():''')

with open('/Users/apple/Desktop/Quizz/quiz/views.py', 'w') as f:
    f.write(new_content)

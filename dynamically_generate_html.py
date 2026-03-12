def dynamically_generate_html(lst, stage):
    qtext = lst[0]
    qtype = lst[1]

    base_class = "form-input"

    if qtype == "text":
        html = f"""
        <label class="q-label" for="q{stage}">{qtext}</label><br>
        <input class="{base_class}" type="text" id="q{stage}" name="q{stage}" required><br>
        """

    elif qtype == "number":
        html = f"""
        <label class="q-label" for="q{stage}">{qtext}</label><br>
        <input class="{base_class}" type="number" id="q{stage}" name="q{stage}" required><br>
        """

    elif qtype == "date":
        html = f"""
        <label class="q-label" for="q{stage}">{qtext}</label><br>
        <input class="{base_class}" type="date" id="q{stage}" name="q{stage}" required><br>
        """

    elif qtype == "multichoice":
        options = lst[2]
        html = f"""
        <label class="q-label">{qtext}</label><br>
        <select class="{base_class}" name="q{stage}" required>
        """
        for opt in options:
            html += f'<option value="{opt}">{opt}</option>'
        html += "</select><br>"

    else:
        html = "<p>Unsupported question type</p>"

    return html

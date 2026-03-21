def evaluate(name, sid, schl, email, average, lowest_grade, income, extracurricular):

    scholarships = []
    reasons_fail = []

    if average >= 90 and lowest_grade >= 85:
        scholarships.append("Academic Scholarship")
    else:
        if average < 90:
            reasons_fail.append(f"General average {average} is below 90.")
        if lowest_grade < 85:
            reasons_fail.append(f"Lowest grade {lowest_grade} is below 85.")

    if income <= 15000:
        scholarships.append("Financial Assistance")
    else:
        reasons_fail.append(f"Monthly income P{income:,.2f} exceeds P15,000.")

    if average >= 95 and income <= 10000 and extracurricular:
        scholarships.append("Full Scholarship")
    else:
        missing = []
        if average < 95:
            missing.append("average>=95")
        if income > 10000:
            missing.append("income<=P10k")
        if not extracurricular:
            missing.append("extracurricular")
        if missing:
            reasons_fail.append(
                "Full Scholarship needs: " + ", ".join(missing))

    reasons_fail = list(dict.fromkeys(reasons_fail))
    return len(scholarships) > 0, scholarships, reasons_fail

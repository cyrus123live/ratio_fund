import datetime

today = datetime.date.today()
current_year = today.year
quarters = []

for year in range(2014, current_year + 1):
    for q in range(1, 5):
        if year < current_year:
            # Add all quarters for previous years
            # quarters.append(f"{year}-{3*q:02d}-{31 if q in [1, 4] else 30}")
            quarters.append(f"{year}-{3*q:02d}-{30 if q in [1, 4] else 29}")
        else:
            # For current year, check if quarter end has passed
            if q == 1:
                q_date = datetime.date(year, 3, 31)
            elif q == 2:
                q_date = datetime.date(year, 6, 30)
            elif q == 3:
                q_date = datetime.date(year, 9, 30)
            else:  # q == 4
                q_date = datetime.date(year, 12, 31)
            
            if q_date <= today:
                quarters.append(f"{year}-{q_date.month:02d}-{q_date.day:02d}")

print(quarters)

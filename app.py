import streamlit as st
import pandas as pd
import numpy as np
import altair as alt  # Using Altair for better chart customization

# EMI Calculation
def calculate_emi(principal, rate, tenure):
    monthly_rate = rate / (12 * 100)  # Convert annual rate to monthly
    num_payments = tenure * 12  # Convert tenure to months
    emi = (principal * monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    return round(emi, 2), num_payments  # Round EMI to 2 decimals

# Amortization with extra payments
def amortization_schedule(principal, rate, tenure, extra_payments=None):
    emi, num_payments = calculate_emi(principal, rate, tenure)
    monthly_rate = rate / (12 * 100)

    schedule = []
    balance = principal
    total_interest = 0
    for month in range(1, int(num_payments) + 1):
        interest = round(balance * monthly_rate, 2)  # Round interest to 2 decimals
        principal_payment = round(emi - interest, 2)  # Round principal payment to 2 decimals
        if extra_payments and month in extra_payments:
            principal_payment += extra_payments[month]
            principal_payment = round(principal_payment, 2)  # Round total principal payment to 2 decimals
        balance -= principal_payment
        total_interest += interest
        schedule.append({
            'Month': month,
            'Interest Payment': interest,
            'Principal Payment': principal_payment,
            'Remaining Balance': max(0, round(balance, 2))  # Ensure remaining balance never goes below 0
        })
        if balance <= 0:
            break
    return pd.DataFrame(schedule), round(total_interest, 2), len(schedule)  # Return total months as well

# Streamlit app layout
st.title('Mortgage Loan Calculator')

loan_amount = st.number_input("Total Loan Amount", value=3500000)
loan_tenure = st.number_input("Loan Tenure (years)", value=20)
interest_rate = st.number_input("Interest Rate (%)", value=9.35)
extra_payment = st.text_input("Extra Payments (format: {month: amount})")

# Parse extra payments input
if extra_payment:
    extra_payment_dict = eval(extra_payment)
else:
    extra_payment_dict = {}

# Calculate without extra payments (to compare interest and months)
schedule_no_extra, total_interest_no_extra, total_months_no_extra = amortization_schedule(loan_amount, interest_rate, loan_tenure)

# Calculate with extra payments
schedule_with_extra, total_interest, total_months = amortization_schedule(loan_amount, interest_rate, loan_tenure, extra_payment_dict)

# Clip any negative remaining balances
schedule_no_extra['Remaining Balance'] = schedule_no_extra['Remaining Balance'].clip(lower=0)
schedule_with_extra['Remaining Balance'] = schedule_with_extra['Remaining Balance'].clip(lower=0)

# Add Year column
schedule_no_extra['Year'] = (schedule_no_extra['Month'] / 12).apply(np.floor)
schedule_with_extra['Year'] = (schedule_with_extra['Month'] / 12).apply(np.floor)

# Group data by year for plotting
chart_data_no_extra = schedule_no_extra[['Year', 'Remaining Balance']].groupby('Year').last().reset_index()
chart_data_with_extra = schedule_with_extra[['Year', 'Remaining Balance']].groupby('Year').last().reset_index()

# Plot the area chart for both scenarios
st.subheader("Principal Reduction Area Chart", divider=True)

# Combine the two datasets
chart_data_no_extra['Scenario'] = 'Without Extra Payments'
chart_data_with_extra['Scenario'] = 'With Extra Payments'
combined_chart_data = pd.concat([chart_data_no_extra, chart_data_with_extra])

# Plot using Altair for dual scenarios
chart = alt.Chart(combined_chart_data).mark_area().encode(
    x=alt.X('Year:O', title='Year'),
    y=alt.Y('Remaining Balance:Q', title='Remaining Balance (Principal)'),
    color=alt.Color('Scenario:N', scale=alt.Scale(domain=['Without Extra Payments', 'With Extra Payments'],
                                                  range=['#1f77b4', '#aec7e8'])),  # Light color for extra payments
    opacity=alt.condition(
        alt.datum.Scenario == 'With Extra Payments', alt.value(0.6), alt.value(1.0))  # Lighten the "with extra" scenario
).properties(
    width=700,
    height=400
)

st.altair_chart(chart, use_container_width=True)

# Calculate interest saved and months reduced
interest_saved = total_interest_no_extra - total_interest
months_reduced = total_months_no_extra - total_months

interest_saved_round = round(interest_saved, 2)

# Display saved months and interest
st.write(f"Total Interest Paid Without Extra Payments: ₹{total_interest_no_extra}")
st.write(f"Total Interest Paid With Extra Payments: ₹{total_interest}")
st.write(f"Interest Saved: ₹{interest_saved_round}")
st.write(f"Months Reduced: {months_reduced} months")

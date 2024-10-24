import streamlit as st
import pandas as pd
import numpy as np


# EMI Calculation
def calculate_emi(principal, rate, tenure):
    monthly_rate = rate / (12 * 100)  # Convert annual rate to monthly
    num_payments = tenure * 12  # Convert tenure to months
    emi = (principal * monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    return emi, num_payments


# Amortization with extra payments
def amortization_schedule(principal, rate, tenure, extra_payments=None):
    emi, num_payments = calculate_emi(principal, rate, tenure)
    monthly_rate = rate / (12 * 100)

    schedule = []
    balance = principal
    total_interest = 0
    for month in range(1, int(num_payments) + 1):
        interest = balance * monthly_rate
        principal_payment = emi - interest
        if extra_payments and month in extra_payments:
            principal_payment += extra_payments[month]
        balance -= principal_payment
        total_interest += interest
        schedule.append({
            'Month': month,
            'Interest Payment': interest,
            'Principal Payment': principal_payment,
            'Remaining Balance': balance
        })
        if balance <= 0:
            break
    return pd.DataFrame(schedule), total_interest

# Streamlit app layout
st.title('Mortgage Loan Calculator')

loan_amount = st.number_input("Total Loan Amount", value=500000)
loan_tenure = st.number_input("Loan Tenure (years)", value=20)
interest_rate = st.number_input("Interest Rate (%)", value=7.5)
extra_payment = st.text_input("Extra Payments (format: {month: amount})", value="")

# Parse extra payments input
if extra_payment:
    extra_payment_dict = eval(extra_payment)
else:
    extra_payment_dict = {}

# Calculate EMI and Amortization
schedule, total_interest = amortization_schedule(loan_amount, interest_rate, loan_tenure, extra_payment_dict)

# Display the amortization schedule
st.write("Amortization Schedule")
st.dataframe(schedule)

# Display principal reduction over time (chart)
schedule['Year'] = (schedule['Month'] / 12).apply(np.floor)
chart_data = schedule[['Year', 'Principal Payment']].groupby('Year').sum()
st.area_chart(chart_data)

# Display saved months and interest
st.write(f"Total Interest Paid: {total_interest}")


import streamlit as st
import pandas as pd
import numpy as np


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
            'Remaining Balance': round(balance, 2)  # Round remaining balance to 2 decimals
        })
        if balance <= 0:
            break
    return pd.DataFrame(schedule), round(total_interest, 2)  # Round total interest to 2 decimals

# Streamlit app layout
st.title('Mortgage Loan Calculator')

loan_amount = st.number_input("Total Loan Amount", value=3500000)
loan_tenure = st.number_input("Loan Tenure (years)", value=20)
interest_rate = st.number_input("Interest Rate (%)",value=9.35)
extra_payment = st.text_input("Extra Payments (format: {month: amount})")

# Parse extra payments input
if extra_payment:
    extra_payment_dict = eval(extra_payment)
else:
    extra_payment_dict = {}

# Calculate EMI and Amortization
schedule, total_interest = amortization_schedule(loan_amount, interest_rate, loan_tenure, extra_payment_dict)

# Display the amortization schedule
st.subheader("Amortization Schedule", divider=True)
st.dataframe(schedule.style.format({
    'Interest Payment': "₹{:,.2f}",
    'Principal Payment': "₹{:,.2f}",
    'Remaining Balance': "₹{:,.2f}"
}))

# Display principal reduction over time (chart)
schedule['Year'] = (schedule['Month'] / 12).apply(np.floor)
chart_data = schedule[['Year', 'Principal Payment']].groupby('Year').sum().reset_index()
chart_data['Principal Payment'] = chart_data['Principal Payment'].apply(lambda x: round(x, 2))

st.subheader("Area Chart", divider=True)
st.area_chart(chart_data.set_index('Year'))

# Display saved months and interest
st.write(f"Total Interest Paid: ₹{total_interest}")

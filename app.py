import streamlit as st
import pandas as pd
import numpy as np
import locale

# Attempt to set the locale
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # Change to a locale that is available on your system
except locale.Error:
    st.error("The requested locale is not supported on this system. Defaulting to the system's locale.")
    locale.setlocale(locale.LC_ALL, '')  # Fallback to default locale


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

    # Ensure extra_payments is a dictionary
    extra_payments = extra_payments or {}

    schedule = []
    balance = principal
    total_interest = 0
    for month in range(1, int(num_payments) + 1):
        interest = round(balance * monthly_rate, 2)  # Round interest to 2 decimals
        principal_payment = round(emi - interest, 2)  # Round principal payment to 2 decimals
        extra_payment_amount = extra_payments.get(month, 0)  # Get extra payment for the month
        principal_payment += extra_payment_amount  # Add extra payment to principal payment
        balance -= principal_payment
        total_interest += interest

        schedule.append({
            'Month': month,
            'Interest Payment': interest,
            'Principal Payment': principal_payment,
            'Extra Payment': extra_payment_amount,  # Add extra payment to the schedule
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
    try:
        extra_payment_dict = eval(extra_payment)  # Use eval carefully in a real app
    except:
        extra_payment_dict = {}
else:
    extra_payment_dict = {}

# Calculate without extra payments (to compare interest and months)
schedule_no_extra, total_interest_no_extra, total_months_no_extra = amortization_schedule(loan_amount, interest_rate, loan_tenure)

# Calculate with extra payments
schedule, total_interest, total_months = amortization_schedule(loan_amount, interest_rate, loan_tenure, extra_payment_dict)

# Display the amortization schedule
st.subheader("Amortization Schedule", divider=True)
st.dataframe(schedule.style.format({
    'Interest Payment': "₹{:,.2f}",
    'Principal Payment': "₹{:,.2f}",
    'Extra Payment': "₹{:,.2f}",
    'Remaining Balance': "₹{:,.2f}"
}),use_container_width=True)

st.subheader("Principal Reduction Area Chart", divider=True)

# Clip any negative remaining balances
schedule['Remaining Balance'] = schedule['Remaining Balance'].clip(lower=0)

# Plot the area chart with remaining principal (balance) over time
schedule['Year'] = (schedule['Month'] / 12).apply(np.floor)
chart_data = schedule[['Year', 'Remaining Balance']].groupby('Year').last().reset_index()

# Plot the area chart
st.area_chart(chart_data.set_index('Year'))

# Calculate interest saved and months reduced
interest_saved = total_interest_no_extra - total_interest
months_reduced = total_months_no_extra - total_months

interest_saved_round = round(interest_saved, 2)

# Formatting the numbers using locale
try:
    formatted_currency = locale.currency(interest_saved_round, grouping=True)
except ValueError as e:
    st.error(f"Currency formatting error: {e}")
    formatted_currency = f"${interest_saved_round:,.2f}"  # Fallback to manual formatting

# Display saved months and interest
st.write(f"Total Interest Paid Without Extra Payments: **₹{total_interest_no_extra}**")
st.write(f"Total Interest Paid With Extra Payments: **₹{total_interest}**")
st.write(f"Interest Saved: **₹{formatted_currency}**")
st.write(f"Months Reduced: **{months_reduced} months**")

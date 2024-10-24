import streamlit as st
import pandas as pd
import numpy as np

# Corrected custom function to format numbers in Indian numerical system
def format_inr(value):
    value_str = f"{value:,.2f}"  # Format as comma-separated string
    int_part, dec_part = value_str.split(".")  # Split into integer and decimal parts
    int_part = int(int_part.replace(",", ""))  # Remove existing commas for further formatting

    # Handle negative numbers
    if int_part < 0:
        sign = "-"
        int_part = abs(int_part)
    else:
        sign = ""

    # Format integer part in the Indian numbering system (thousands, lakhs, crores)
    int_part_str = f"{int_part:,}"
    int_part_str = int_part_str.replace(",", "X")  # Temporarily replace commas

    # Add commas for Indian format (first 3 digits then every 2 digits)
    if len(int_part_str) > 3:
        int_part_str = int_part_str[:-3].replace("X", "") + "," + int_part_str[-3:]
        int_part_str = int_part_str[:-6] + ",".join([int_part_str[-6 + i: -4 + i] for i in range(0, len(int_part_str[-6:]), 2)])

    return f"{sign}{int_part_str}.{dec_part}"  # Return formatted value with decimals


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
    months_saved = 0
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
            months_saved = num_payments - month  # Calculate how many months are saved
            break
    return pd.DataFrame(schedule), round(total_interest, 2), months_saved  # Round total interest to 2 decimals


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

# Calculate EMI and Amortization without extra payments (for comparison)
_, total_interest_no_extra, _ = amortization_schedule(loan_amount, interest_rate, loan_tenure)

# Calculate EMI and Amortization with extra payments
schedule, total_interest_with_extra, months_saved = amortization_schedule(loan_amount, interest_rate, loan_tenure, extra_payment_dict)

# Display the amortization schedule
st.subheader("Amortization Schedule", divider=True)
st.dataframe(schedule.style.format({
    'Interest Payment': lambda x: "₹" + format_inr(x),
    'Principal Payment': lambda x: "₹" + format_inr(x),
    'Remaining Balance': lambda x: "₹" + format_inr(x)
}))

st.subheader("Principal Reduction Area Chart", divider=True)

# Clip any negative remaining balances
schedule['Remaining Balance'] = schedule['Remaining Balance'].clip(lower=0)

# Plot the area chart with remaining principal (balance) over time
schedule['Year'] = (schedule['Month'] / 12).apply(np.floor)
chart_data = schedule[['Year', 'Remaining Balance']].groupby('Year').last().reset_index()

# Plot the area chart
st.area_chart(chart_data.set_index('Year'))

# Total Interest Paid with Extra Payments
st.write(f"Total Interest Paid (with extra payments): ₹{format_inr(total_interest_with_extra)}")

# Interest Saved Calculation
interest_saved = total_interest_no_extra - total_interest_with_extra
st.write(f"Total Interest Saved: ₹{format_inr(interest_saved)}")

# Display saved months and interest saved
st.write(f"Months Reduced Due to Extra Payments: {months_saved} months")

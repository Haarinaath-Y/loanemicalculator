import streamlit as st
import pandas as pd
import numpy as np
from babel.numbers import format_currency
import re

# Currency-Locale Mapping
CURRENCY_LOCALE_MAP = {
    'INR': 'en_IN',  # Indian Rupee
    'USD': 'en_US',  # US Dollar
    'EUR': 'fr_FR',  # Euro (France)
    'GBP': 'en_GB',  # British Pound
    'JPY': 'ja_JP',  # Japanese Yen
    'CNY': 'zh_CN',  # Chinese Yuan
    'AUD': 'en_AU',  # Australian Dollar
    'CAD': 'en_CA',  # Canadian Dollar
    'CHF': 'de_CH'   # Swiss Franc (German-speaking part of Switzerland)
}

# Initialize session state for extra payments list if not already done
if 'extra_payments' not in st.session_state:
    st.session_state.extra_payments = []  # List to store extra payments (month and amount)


# Add a new empty extra payment row
def add_payment_row():
    st.session_state.extra_payments.append({"month": None, "amount": 0})


# Remove an extra payment row by index
def remove_payment_row(index):
    if index < len(st.session_state.extra_payments):
        del st.session_state.extra_payments[index]  # Delete entry at the specified index


def currency(amount, currency_selection, locale):
    a = format_currency(amount, currency_selection, locale=locale)
    return a


# Helper function to strip currency symbols, commas, and convert to float
def strip_currency(value):
    # Use regular expressions to remove non-numeric characters (except '.')
    return float(re.sub(r'[^\d.]+', '', value))


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


def main():

    # Streamlit app layout
    st.set_page_config(page_title='Loan EMI Calculator', page_icon='💸')
    st.title('💸 Loan EMI Calculator')

    # Currency selection dropdown
    selected_currency = st.selectbox("Select Currency", options=list(CURRENCY_LOCALE_MAP.keys()))

    # Fetch locale based on selected currency
    locale = CURRENCY_LOCALE_MAP[selected_currency]

    loan_amount = st.number_input("Total Loan Amount", value=3500000)
    loan_tenure = st.number_input("Loan Tenure (years)", value=20)
    interest_rate = st.number_input("Interest Rate (%)", value=9.35)

    emi, num_payments = calculate_emi(loan_amount, interest_rate, loan_tenure)
    emi = currency(emi, selected_currency, locale)
    st.info(f'Monthly Installment: **{emi}**')

    # Extra payments input section
    st.subheader("Extra Payments", divider=True)

    # Display current extra payments
    for i, payment in enumerate(st.session_state.extra_payments):
        col1, col2, col3 = st.columns([1, 1, 0.1])

        # Month selector (1 to max tenure in months)
        payment['month'] = col1.number_input(f"Month {i+1}", min_value=1, max_value=loan_tenure*12, key=f"month_{i}")

        # Amount input
        payment['amount'] = col2.number_input(f"Amount {i+1}", min_value=0.0, key=f"amount_{i}")

        # Add empty space to push the delete button to the bottom
        with col3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # Adjust 'height' as needed
            if st.button(":material/delete:", key=f"remove_{i}"):
                remove_payment_row(i)
                st.rerun()  # Rerun to refresh the UI after deletion

    # Add new extra payment row button
    if st.button("👉 Click here to Add Extra Payments"):
        add_payment_row()
        st.rerun()

    extra_payment_dict = {payment['month']: payment['amount'] for payment in st.session_state.extra_payments if payment['month']}

    # Display the amortization schedule
    st.subheader("Amortization Schedule", divider=True)

    # Calculate without extra payments (to compare interest and months)
    schedule_no_extra, total_interest_no_extra, total_months_no_extra = amortization_schedule(loan_amount, interest_rate, loan_tenure)

    # Calculate with extra payments
    schedule, total_interest, total_months = amortization_schedule(loan_amount, interest_rate, loan_tenure, extra_payment_dict)

    # Format currency in the selected currency and locale
    schedule['Interest Payment'] = schedule['Interest Payment'].apply(lambda x: format_currency(x, selected_currency, locale=locale))
    schedule['Principal Payment'] = schedule['Principal Payment'].apply(lambda x: format_currency(x, selected_currency, locale=locale))
    schedule['Extra Payment'] = schedule['Extra Payment'].apply(lambda x: format_currency(x, selected_currency, locale=locale))
    schedule['Remaining Balance'] = schedule['Remaining Balance'].apply(lambda x: format_currency(x, selected_currency, locale=locale))

    st.dataframe(schedule, use_container_width=True, hide_index=True)

    # Display Area Chart
    st.subheader("Principal Reduction Area Chart", divider=True)

    # Apply the strip_currency function
    schedule['Remaining Balance'] = schedule['Remaining Balance'].apply(strip_currency)

    # Plot the area chart with remaining principal (balance) over time
    schedule['Year'] = (schedule['Month'] / 12).apply(np.floor)
    chart_data = schedule[['Year', 'Remaining Balance']].groupby('Year').last().reset_index()

    # Plot the area chart
    st.area_chart(chart_data.set_index('Year'))

    # Calculate interest saved and months reduced
    interest_saved = total_interest_no_extra - total_interest
    months_reduced = total_months_no_extra - total_months

    interest_saved_round = round(interest_saved, 2)

    total_interest_format = currency(total_interest, selected_currency, locale=locale)
    total_interest_no_extra_format = currency(total_interest_no_extra, selected_currency, locale=locale)
    interest_saved = currency(interest_saved_round, selected_currency, locale=locale)

    total_amount_paid = total_interest + loan_amount
    total_amount_paid = currency(total_amount_paid, selected_currency, locale=locale)

    total_amount_no_extra_paid = total_interest_no_extra + loan_amount
    total_amount_no_extra_paid = currency(total_amount_no_extra_paid, selected_currency, locale=locale)

    # Display saved months and interest
    st.subheader('Loan Details With Extra Payments', divider=True)

    st.write(f"Total Amount Paid With Extra Payments: **{total_amount_paid}**")
    st.write(f"Total Interest Paid With Extra Payments: **{total_interest_format}**")
    st.write(f"Interest Saved: **{interest_saved}**")
    st.write(f"Months Reduced: **{months_reduced} months**")

    st.subheader('Loan Details Without Extra Payments', divider=True)
    st.write(f"Total Amount Paid Without Extra Payments: **{total_amount_no_extra_paid}**")
    st.write(f"Total Interest Paid Without Extra Payments: **{total_interest_no_extra_format}**")


if __name__ == '__main__':
    main()

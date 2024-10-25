import streamlit as st
import pandas as pd
import numpy as np
from babel.numbers import format_currency
import re
import altair as alt


# Currency-Locale Mapping
CURRENCY_LOCALE_MAP = {
    'USD': 'en_US',  # US Dollar
    'EUR': 'fr_FR',  # Euro (France)
    'INR': 'en_IN',  # Indian Rupee
    'GBP': 'en_GB',  # British Pound
    'JPY': 'ja_JP',  # Japanese Yen
    'CNY': 'zh_CN',  # Chinese Yuan
    'AUD': 'en_AU',  # Australian Dollar
    'CAD': 'en_CA',  # Canadian Dollar
    'CHF': 'de_CH'   # Swiss Franc (German-speaking part of Switzerland)
}


def currency(amount, currency_selection, locale):
    a = format_currency(amount, currency_selection, locale=locale)
    return a


# Helper function to strip currency symbols, commas, and convert to float
def strip_currency(value):
    if isinstance(value, float):
        return value  # If already a float, return it directly
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
    st.set_page_config(page_title='Mortgage Loan Calculator', page_icon='💸')
    st.title('Mortgage Loan Calculator')

    # Currency selection dropdown
    selected_currency = st.selectbox("Select Currency", options=list(CURRENCY_LOCALE_MAP.keys()))

    # Fetch locale based on selected currency
    locale = CURRENCY_LOCALE_MAP[selected_currency]

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

    emi, num_payments = calculate_emi(loan_amount, interest_rate, loan_tenure)
    emi = currency(emi, selected_currency, locale)
    st.info(f'Monthly Installment: **{emi}**')

    # Calculate without extra payments (to compare interest and months)
    schedule_no_extra, total_interest_no_extra, total_months_no_extra = amortization_schedule(loan_amount, interest_rate, loan_tenure)

    # Calculate with extra payments
    schedule_extra, total_interest_extra, total_months_extra = amortization_schedule(loan_amount, interest_rate, loan_tenure, extra_payment_dict)

    # Add labels to distinguish between schedules
    schedule_no_extra['Type'] = 'Without Extra Payments'
    schedule_extra['Type'] = 'With Extra Payments'

    # Combine the two schedules into one DataFrame
    combined_schedule = pd.concat([schedule_no_extra, schedule_extra])

    # Convert 'Month' to 'Year' for the x-axis
    combined_schedule['Year'] = (combined_schedule['Month'] / 12).apply(np.floor)

    # Strip currency formatting from the 'Remaining Balance' column
    combined_schedule['Remaining Balance'] = combined_schedule['Remaining Balance'].apply(strip_currency)

    # Display the amortization schedule
    st.subheader("Amortization Schedule", divider=True)

    # Format currency in the selected currency and locale
    schedule_extra['Interest Payment'] = schedule_extra['Interest Payment'].apply(lambda x: format_currency(x, selected_currency, locale=locale))
    schedule_extra['Principal Payment'] = schedule_extra['Principal Payment'].apply(lambda x: format_currency(x, selected_currency, locale=locale))
    schedule_extra['Extra Payment'] = schedule_extra['Extra Payment'].apply(lambda x: format_currency(x, selected_currency, locale=locale))
    schedule_extra['Remaining Balance'] = schedule_extra['Remaining Balance'].apply(lambda x: format_currency(x, selected_currency, locale=locale))

    st.dataframe(schedule_extra, use_container_width=True)

    st.subheader("Principal Reduction Area Chart", divider=True)



    # Create the Altair chart
    base_chart = alt.Chart(combined_schedule).mark_area(opacity=0.5).encode(
        x=alt.X('Year:Q', title='Year'),
        y=alt.Y('Remaining Balance:Q', title='Remaining Balance'),
        color='Type:N',  # Color by Type (With vs Without Extra Payments)
        tooltip=['Year', 'Remaining Balance', 'Type']
    ).properties(
        width=600,
        height=400
    )

    # Display the chart in Streamlit
    st.altair_chart(base_chart, use_container_width=True)

    # Calculate interest saved and months reduced
    interest_saved = total_interest_no_extra - total_interest_extra
    months_reduced = total_months_no_extra - total_months_extra

    interest_saved_round = round(interest_saved, 2)

    total_interest_format = currency(total_interest, selected_currency, locale=locale)
    total_interest_no_extra_format = currency(total_interest_no_extra, selected_currency, locale=locale)
    interest_saved = currency(interest_saved_round, selected_currency, locale=locale)

    total_amount_paid = total_interest + loan_amount
    total_amount_paid = currency(total_amount_paid, selected_currency, locale=locale)

    total_amount_no_extra_paid = total_interest_no_extra + loan_amount
    total_amount_no_extra_paid = currency(total_amount_no_extra_paid, selected_currency, locale=locale)

    st.subheader('Loan Details With Extra Payments', divider=True)
    # Display saved months and interest
    st.write(f"Total Amount Paid With Extra Payments: **{total_amount_paid}**")
    st.write(f"Total Interest Paid With Extra Payments: **{total_interest_format}**")
    st.write(f"Interest Saved: **{interest_saved}**")
    st.write(f"Months Reduced: **{months_reduced} months**")

    st.subheader('Loan Details Without Extra Payments', divider=True)
    st.write(f"Total Amount Paid Without Extra Payments: **{total_amount_no_extra_paid}**")
    st.write(f"Total Interest Paid Without Extra Payments: **{total_interest_no_extra_format}**")


if __name__ == '__main__':
    main()

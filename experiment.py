import streamlit as st

# Initialize session state for extra payments list if not already done
if 'extra_payments' not in st.session_state:
    st.session_state.extra_payments = []  # List to store extra payments (month and amount)

# Add a new empty extra payment row
def add_payment_row():
    st.session_state.extra_payments.append({"month": None, "amount": 0})

# Remove an extra payment row by index
def remove_payment_row(index):
    if index < len(st.session_state.extra_payments):
        st.session_state.extra_payments.pop(index)

# Title and inputs for main loan parameters
st.title("Mortgage Loan Calculator with Extra Payments")
loan_amount = st.number_input("Total Loan Amount", value=3500000)
loan_tenure = st.number_input("Loan Tenure (years)", value=20)
interest_rate = st.number_input("Interest Rate (%)", value=9.35)

# Extra payments input section
st.subheader("Extra Payments")

# Display current extra payments
for i, payment in enumerate(st.session_state.extra_payments):
    col1, col2, col3 = st.columns([1, 1, 0.2])

    # Month selector (1 to max tenure in months)
    payment['month'] = col1.number_input(f"Month {i+1}", min_value=1, max_value=loan_tenure*12, key=f"month_{i}")

    # Amount input
    payment['amount'] = col2.number_input(f"Amount {i+1}", min_value=0.0, key=f"amount_{i}")

    # Remove button
    if col3.button("Remove", key=f"remove_{i}"):
        remove_payment_row(i)

# Add new extra payment row button
if st.button("Add Payment"):
    add_payment_row()

st.dataframe(st.session_state.extra_payments)
# Display extra payments
st.write("Extra Payments:", st.session_state.extra_payments)

# Pass st.session_state.extra_payments into your amortization calculation function as needed

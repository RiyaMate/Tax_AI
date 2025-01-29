import streamlit as st
import numpy as np
import pandas as pd
st.title('Hello, Streamlit!')
st.write('This is a simple Streamlit app.')
df = pd.DataFrame({
    'first column': [1, 2, 3, 4],
    'second column': [10, 20, 30, 40]
    },index=['first', 'second', 'third', 'fourth'])
df
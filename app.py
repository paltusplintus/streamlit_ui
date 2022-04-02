import streamlit as st
from neointerface import NeoInterface

x = st.slider('Select a value')
st.write(x, 'squared is', x * x)

neo = NeoInterface()
st.write(str(neo.query("RETURN 1")))
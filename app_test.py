import streamlit as st
from neointerface import NeoInterface

x = st.slider('Select a value')
st.write(x, 'squared is', x * x)

neo = NeoInterface()
st.write(str(neo.query("RETURN 1")))
st.write(str(neo.query("UNWIND range(1,1000) as i RETURN i")))